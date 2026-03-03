import pandas as pd
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)


async def _get_llm_client():
    """Get the Groq LLM client. Returns None if not configured."""
    try:
        from openai import AsyncOpenAI
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        return AsyncOpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    except Exception:
        return None


async def _llm_generate(client, prompt, max_tokens=300):
    """Call the LLM and return the response text. Returns None on failure."""
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a concise data analysis expert. Provide clear, actionable insights. Be specific with numbers. No markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=max_tokens,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        return None

def generate_dataset_summary(df, column_types):
    """
    Generate a detailed summary of the dataset.
    """
    summary = {
        "overview": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": len(column_types.get("numeric", [])),
            "categorical_columns": len(column_types.get("categorical", [])),
            "datetime_columns": len(column_types.get("datetime", []))
        },
        "column_details": []
    }
    
    # Add details for each column
    for col in df.columns:
        col_info = {
            "name": col,
            "type": "unknown",
            "unique_values": int(df[col].nunique()),
            "missing_values": int(df[col].isnull().sum()),
            "missing_percent": round(df[col].isnull().mean() * 100, 2)
        }
        
        # Determine type
        if col in column_types.get("numeric", []):
            col_info["type"] = "numeric"
            col_info["min"] = float(df[col].min())
            col_info["max"] = float(df[col].max())
            col_info["mean"] = float(df[col].mean())
            col_info["median"] = float(df[col].median())
        elif col in column_types.get("categorical", []):
            col_info["type"] = "categorical"
            col_info["top_values"] = df[col].value_counts().head(3).to_dict()
        elif col in column_types.get("datetime", []):
            col_info["type"] = "datetime"
            col_info["min_date"] = str(df[col].min())
            col_info["max_date"] = str(df[col].max())
        
        summary["column_details"].append(col_info)
    
    return summary

def _build_chart_data_summary(chart, df):
    """Build a concise text summary of a chart's data for the LLM."""
    chart_type = chart.get("type", "")
    x_col = chart.get("x")
    y_col = chart.get("y")
    data = chart.get("data", [])
    stats = chart.get("statistics", {})
    correlation = chart.get("correlation")
    column = chart.get("column", y_col)

    lines = [f"Chart type: {chart_type}", f"Title: {chart.get('title', 'N/A')}"]

    # Use pre-aggregated data from the chart (max 15 rows for prompt brevity)
    if data:
        sample = data[:15]
        lines.append(f"Data points ({len(data)} total, showing up to 15):")
        for row in sample:
            parts = [f"{k}: {v}" for k, v in row.items()]
            lines.append(f"  {', '.join(parts)}")

    # Add statistics if available
    if stats:
        lines.append(f"Statistics: mean={stats.get('mean')}, median={stats.get('median')}, "
                      f"std={stats.get('std')}, min={stats.get('min')}, max={stats.get('max')}")

    if correlation is not None:
        lines.append(f"Correlation coefficient: {correlation}")

    # For charts without pre-aggregated data, pull from the dataframe
    if not data and x_col and y_col and x_col in df.columns and y_col in df.columns:
        if chart_type == "line":
            col_data = df[y_col].dropna()
            lines.append(f"{y_col} — min: {col_data.min():.2f}, max: {col_data.max():.2f}, "
                          f"mean: {col_data.mean():.2f}, first: {col_data.iloc[0]:.2f}, last: {col_data.iloc[-1]:.2f}")
        elif chart_type == "scatter":
            corr = df[x_col].corr(df[y_col])
            lines.append(f"Correlation: {corr:.3f}")

    return "\n".join(lines)


async def generate_chart_interpretations(charts, df, column_types):
    """
    Generate LLM-powered interpretations for each chart.
    Falls back to rule-based interpretations if LLM is unavailable.
    """
    import asyncio
    client = await _get_llm_client()
    
    tasks = []
    for chart in charts:
        if client:
            data_summary = _build_chart_data_summary(chart, df)
            prompt = (
                f"Analyze this chart and write a 2-3 sentence interpretation that a business user would find useful.\n"
                f"Mention the most important pattern, the key numbers, and one actionable takeaway.\n\n"
                f"{data_summary}"
            )
            tasks.append(_llm_generate(client, prompt, max_tokens=200))
        else:
            tasks.append(asyncio.sleep(0, result=None)) # Placeholder

    llm_results = await asyncio.gather(*tasks)
    
    interpretations = []
    for i, chart in enumerate(charts):
        title = chart.get("title", "")
        chart_type = chart.get("type")
        llm_text = llm_results[i]

        # --- Fallback: rule-based ---
        if not llm_text:
            llm_text = _fallback_interpretation(chart, df)

        interpretations.append({
            "chart_title": title,
            "chart_type": chart_type,
            "interpretation": llm_text
        })

    return interpretations


def _fallback_interpretation(chart, df):
    """Rule-based fallback interpretation when LLM is unavailable."""
    chart_type = chart.get("type")
    x_col = chart.get("x")
    y_col = chart.get("y")

    if chart_type == "line":
        if y_col and y_col in df.columns:
            trend = "increasing" if df[y_col].iloc[-1] > df[y_col].iloc[0] else "decreasing"
            return (
                f"This line chart shows the trend of {y_col} over time. "
                f"The overall trend appears to be {trend}, helping identify temporal patterns and seasonality in the data."
            )

    elif chart_type in ("bar", "histogram", "horizontalBar"):
        data = chart.get("data", [])
        if data and y_col:
            top = max(data, key=lambda r: r.get(y_col, 0)) if data else {}
            top_label = top.get(x_col, "N/A")
            return (
                f"This bar chart compares {y_col} across different {x_col} categories. "
                f"'{top_label}' shows the highest value."
            )

    elif chart_type == "scatter":
        corr = chart.get("correlation")
        if corr is not None:
            strength = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
            direction = "positive" if corr > 0 else "negative"
            return (
                f"This scatter plot reveals a {strength} {direction} correlation (r={corr:.2f}) "
                f"between {x_col} and {y_col}."
            )

    elif chart_type in ("pie", "donut"):
        data = chart.get("data", [])
        if data:
            top = max(data, key=lambda r: r.get(y_col or "count", 0))
            return (
                f"This chart shows the distribution of {x_col}. "
                f"'{top.get(x_col, 'N/A')}' is the largest segment."
            )

    elif chart_type == "heatmap":
        return "This heatmap shows correlations between numeric variables. Darker colors indicate stronger relationships."

    elif chart_type == "boxPlot":
        data = chart.get("data", [])
        if data:
            d = data[0]
            return (
                f"This box plot of {d.get('name', '')} shows the median at {d.get('median')}, "
                f"with data ranging from {d.get('min')} to {d.get('max')}. "
                f"There are {len(d.get('outliers', []))} outlier(s)."
            )

    return f"This {chart_type} chart visualizes {chart.get('title', 'the data')}."

async def generate_conclusion(df, column_types, summary_stats, insights):
    """
    Generate a conclusion section summarizing the dataset, enhanced with LLM when available.
    """
    numeric_cols = column_types.get("numeric", [])
    categorical_cols = column_types.get("categorical", [])
    datetime_cols = column_types.get("datetime", [])
    
    conclusion = {
        "title": "Dataset Conclusion",
        "summary": "",
        "key_findings": [],
        "data_characteristics": []
    }

    # --- Try LLM-powered conclusion ---
    client = await _get_llm_client()
    if client:
        context_lines = [
            f"Dataset: {len(df)} rows, {len(df.columns)} columns.",
            f"Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols[:8])}",
            f"Categorical columns ({len(categorical_cols)}): {', '.join(categorical_cols[:5])}",
            f"Datetime columns ({len(datetime_cols)}): {', '.join(datetime_cols[:3])}",
        ]

        # Add key stats
        for col in numeric_cols[:4]:
            if col in df.columns:
                d = df[col].dropna()
                context_lines.append(f"{col}: mean={d.mean():.2f}, median={d.median():.2f}, "
                                      f"min={d.min():.2f}, max={d.max():.2f}")

        if insights:
            context_lines.append("Insights: " + " | ".join(insights[:6]))

        prompt = (
            "Based on the following dataset information, write:\n"
            "1. A 2-3 sentence summary of the dataset and its significance.\n"
            "2. Exactly 3 key findings (short bullet points).\n"
            "3. Exactly 3 data characteristics (short bullet points).\n\n"
            "Be specific, use numbers, and write for a business audience. No markdown.\n"
            "Format your response as:\n"
            "SUMMARY: ...\n"
            "FINDING: ...\n"
            "FINDING: ...\n"
            "FINDING: ...\n"
            "CHARACTERISTIC: ...\n"
            "CHARACTERISTIC: ...\n"
            "CHARACTERISTIC: ...\n\n"
            + "\n".join(context_lines)
        )

        llm_text = await _llm_generate(client, prompt, max_tokens=400)
        if llm_text:
            lines = llm_text.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line.upper().startswith("SUMMARY:"):
                    conclusion["summary"] = line[len("SUMMARY:"):].strip()
                elif line.upper().startswith("FINDING:"):
                    conclusion["key_findings"].append(line[len("FINDING:"):].strip())
                elif line.upper().startswith("CHARACTERISTIC:"):
                    conclusion["data_characteristics"].append(line[len("CHARACTERISTIC:"):].strip())

            # If parsing succeeded, return early
            if conclusion["summary"] and conclusion["key_findings"]:
                return conclusion
    
    # --- Fallback: rule-based ---
    summary_text = f"This dataset contains {len(df)} records across {len(df.columns)} columns, "
    
    if numeric_cols:
        summary_text += f"including {len(numeric_cols)} numeric variables "
    if categorical_cols:
        summary_text += f"and {len(categorical_cols)} categorical variables. "
    if datetime_cols:
        summary_text += f"Time-series data is available through {len(datetime_cols)} datetime column(s). "
    
    conclusion["summary"] = summary_text
    
    if insights and len(insights) > 0:
        conclusion["key_findings"] = insights[:3]
    
    characteristics = []
    total_missing = df.isnull().sum().sum()
    if total_missing == 0:
        characteristics.append("The dataset is complete with no missing values.")
    else:
        missing_pct = (total_missing / (len(df) * len(df.columns))) * 100
        characteristics.append(f"Data completeness: {100 - missing_pct:.1f}% (minimal missing values handled through imputation).")
    
    if numeric_cols:
        main_numeric = numeric_cols[0]
        if main_numeric in df.columns:
            characteristics.append(
                f"Primary numeric variable '{main_numeric}' ranges from "
                f"{df[main_numeric].min():.2f} to {df[main_numeric].max():.2f}."
            )
    
    if categorical_cols:
        main_cat = categorical_cols[0]
        if main_cat in df.columns:
            n_categories = df[main_cat].nunique()
            characteristics.append(
                f"The '{main_cat}' variable contains {n_categories} distinct categories, "
                f"providing good segmentation for analysis."
            )
    
    conclusion["data_characteristics"] = characteristics
    
    return conclusion
