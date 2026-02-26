"""
Chatbot module for interacting with datasets using Groq API.
Allows users to ask questions about their data and get AI-powered insights.
"""

from openai import OpenAI
import os
import pandas as pd
import json

# Initialize Groq client
def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")
    
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )

def generate_data_context(df, columns, summary, insights):
    """
    Generate a context string describing the dataset for the AI.
    """
    context = []
    
    # Dataset overview
    context.append(f"Dataset Overview:")
    context.append(f"- Total rows: {len(df)}")
    context.append(f"- Total columns: {len(df.columns)}")
    context.append(f"- Column names: {', '.join(df.columns.tolist())}")
    
    # Column types
    context.append(f"\nColumn Types:")
    context.append(f"- Numeric columns: {', '.join(columns.get('numeric', []))}")
    context.append(f"- Categorical columns: {', '.join(columns.get('categorical', []))}")
    context.append(f"- Datetime columns: {', '.join(columns.get('datetime', []))}")
    
    # Summary statistics
    if summary:
        context.append(f"\nSummary Statistics:")
        for key, value in summary.items():
            if key != 'total_rows':
                context.append(f"- {key}: {value}")
    
    # Key insights
    if insights:
        context.append(f"\nKey Insights from the data:")
        for insight in insights[:10]:  # Limit to 10 insights
            context.append(f"- {insight}")
    
    # Sample data (first 5 rows)
    context.append(f"\nSample Data (first 5 rows):")
    sample_df = df.head(5).fillna('N/A')
    for idx, row in sample_df.iterrows():
        row_str = ", ".join([f"{col}: {val}" for col, val in row.items()])
        context.append(f"  Row {idx + 1}: {row_str}")
    
    # Descriptive statistics for numeric columns
    numeric_cols = columns.get('numeric', [])
    if numeric_cols:
        context.append(f"\nNumeric Column Statistics:")
        for col in numeric_cols[:5]:  # Limit to 5 columns
            if col in df.columns:
                col_data = df[col].dropna()
                context.append(f"  {col}:")
                context.append(f"    - Mean: {col_data.mean():.2f}")
                context.append(f"    - Median: {col_data.median():.2f}")
                context.append(f"    - Min: {col_data.min():.2f}")
                context.append(f"    - Max: {col_data.max():.2f}")
                context.append(f"    - Std Dev: {col_data.std():.2f}")
    
    # Value counts for categorical columns
    categorical_cols = columns.get('categorical', [])
    if categorical_cols:
        context.append(f"\nCategorical Column Value Counts:")
        for col in categorical_cols[:3]:  # Limit to 3 columns
            if col in df.columns:
                value_counts = df[col].value_counts().head(5)
                context.append(f"  {col} (top 5):")
                for val, count in value_counts.items():
                    context.append(f"    - {val}: {count}")
    
    return "\n".join(context)


def process_chat_message(message, df, columns, summary, insights, chat_history=None):
    """
    Process a chat message and return an AI-generated response.
    
    Args:
        message: User's question/message
        df: The pandas DataFrame
        columns: Dict with column types
        summary: Summary statistics
        insights: Generated insights
        chat_history: Previous chat messages for context
    
    Returns:
        AI-generated response string
    """
    try:
        client = get_groq_client()
        
        # Generate data context
        data_context = generate_data_context(df, columns, summary, insights)
        
        # Build system message
        system_message = f"""You are a helpful data analysis assistant. You have access to a dataset that the user has uploaded. Your role is to:
1. Answer questions about the data accurately and concisely
2. Provide insights and explanations about patterns in the data
3. Suggest visualizations or analyses that might be useful
4. Explain statistical concepts in simple terms when relevant
5. Help users understand their data better

Here is the context about the current dataset:

{data_context}

Guidelines:
- Be concise but informative
- Use specific numbers and statistics from the data when answering
- If you're not sure about something, say so
- Suggest follow-up questions or analyses when appropriate
- Format numbers appropriately (use commas for thousands, round decimals)
- If asked to perform calculations, use the actual data values provided
"""

        # Build messages array
        messages = [{"role": "system", "content": system_message}]
        
        # Add chat history if available
        if chat_history:
            for chat in chat_history[-10:]:  # Keep last 10 messages for context
                messages.append({
                    "role": chat.get("role", "user"),
                    "content": chat.get("content", "")
                })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Using Llama 3.3 70B model
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        if "GROQ_API_KEY" in error_msg:
            return "Error: Groq API key is not configured. Please set the GROQ_API_KEY environment variable."
        elif "rate limit" in error_msg.lower():
            return "Error: Rate limit exceeded. Please wait a moment and try again."
        else:
            return f"Error processing your request: {error_msg}"


def generate_smart_suggestions(df, columns, insights):
    """
    Generate smart question suggestions based on the data.
    """
    suggestions = []
    
    numeric_cols = columns.get('numeric', [])
    categorical_cols = columns.get('categorical', [])
    datetime_cols = columns.get('datetime', [])
    
    # Basic questions
    suggestions.append("What are the key patterns in this dataset?")
    suggestions.append("Give me a summary of this data.")
    
    # Numeric column questions
    if numeric_cols:
        col = numeric_cols[0]
        suggestions.append(f"What is the average {col}?")
        suggestions.append(f"Are there any outliers in {col}?")
        if len(numeric_cols) >= 2:
            suggestions.append(f"Is there a correlation between {numeric_cols[0]} and {numeric_cols[1]}?")
    
    # Categorical column questions
    if categorical_cols:
        col = categorical_cols[0]
        suggestions.append(f"What is the distribution of {col}?")
        if numeric_cols:
            suggestions.append(f"How does {numeric_cols[0]} vary by {col}?")
    
    # Time series questions
    if datetime_cols and numeric_cols:
        suggestions.append(f"What are the trends over time?")
        suggestions.append(f"Are there any seasonal patterns?")
    
    # Insight-based questions
    if insights:
        suggestions.append("Explain the most important insight from this data.")
    
    return suggestions[:8]  # Return max 8 suggestions


def answer_specific_query(query_type, df, columns, **kwargs):
    """
    Handle specific pre-defined query types for faster responses.
    """
    numeric_cols = columns.get('numeric', [])
    categorical_cols = columns.get('categorical', [])
    
    if query_type == "describe":
        # Return descriptive statistics
        desc = df.describe().to_dict()
        return f"Here are the descriptive statistics:\n{json.dumps(desc, indent=2)}"
    
    elif query_type == "correlation" and len(numeric_cols) >= 2:
        col1 = kwargs.get('col1', numeric_cols[0])
        col2 = kwargs.get('col2', numeric_cols[1])
        corr = df[col1].corr(df[col2])
        strength = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
        direction = "positive" if corr > 0 else "negative"
        return f"The correlation between {col1} and {col2} is {corr:.3f}, indicating a {strength} {direction} relationship."
    
    elif query_type == "top_values" and categorical_cols:
        col = kwargs.get('col', categorical_cols[0])
        top_vals = df[col].value_counts().head(5)
        result = f"Top 5 values in {col}:\n"
        for val, count in top_vals.items():
            result += f"  - {val}: {count}\n"
        return result
    
    elif query_type == "missing":
        missing = df.isnull().sum()
        missing = missing[missing > 0]
        if len(missing) == 0:
            return "There are no missing values in the dataset."
        result = "Missing values by column:\n"
        for col, count in missing.items():
            pct = (count / len(df)) * 100
            result += f"  - {col}: {count} ({pct:.1f}%)\n"
        return result
    
    return None  # Query type not recognized
