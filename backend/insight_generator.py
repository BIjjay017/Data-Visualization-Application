import pandas as pd

def generate_insights(df, summary_stats):
    """
    Generates rule-based insights.
    """
    insights = []
    
    # Extract some summary stats for easy access
    # summary_stats keys are like 'sales_sum', 'sales_mean'
    
    # 1. Trend Insights (Simple comparison if Date exists)
    # We need to know which is the date column. 
    # This function might need column types passed in, or we re-detect.
    # Let's try to infer from df type.
    
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    
    if date_cols and numeric_cols:
        date_col = date_cols[0]
        target_col = numeric_cols[0] # Pick first numeric, often 'sales' or similar
        
        # Sort by date
        df_sorted = df.sort_values(by=date_col)
        
        # Simple Check: First vs Last month/period
        # Let's just do a simple "Increase/Decrease" check between first and last half?
        # Or better: Month over Month if enough data.
        
        # Generic approach: Overall trend (Slope?) or just Max day.
        max_val = df[target_col].max()
        max_date = df_sorted.loc[df_sorted[target_col] == max_val, date_col].iloc[0]
        insights.append(f"Highest {target_col} was observed on {max_date}.")

    # 2. Category Insights
    cat_cols = [col for col in df.columns if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col])]
    if cat_cols and numeric_cols:
        cat_col = cat_cols[0]
        target_col = numeric_cols[0]
        
        # Top Category
        top_cat = df.groupby(cat_col)[target_col].sum().idxmax()
        top_val = df.groupby(cat_col)[target_col].sum().max()
        total_val = df[target_col].sum()
        percentage = (top_val / total_val) * 100
        
        insights.append(f"{top_cat} category leads with {percentage:.1f}% of total {target_col}.")
        
    # 3. Correlation (Simple R check)
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        # Find high correlations
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                c1 = numeric_cols[i]
                c2 = numeric_cols[j]
                r = corr.iloc[i, j]
                if abs(r) > 0.7:
                    strength = "Positive" if r > 0 else "Negative"
                    insights.append(f"Strong {strength} correlation between {c1} and {c2} (r = {r:.2f}).")

    return insights
