import pandas as pd
import numpy as np

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

def generate_chart_interpretations(charts, df, column_types):
    """
    Generate 2-line interpretations for each recommended chart.
    """
    interpretations = []
    
    for chart in charts:
        chart_type = chart.get("type")
        x_col = chart.get("x")
        y_col = chart.get("y")
        
        interpretation = {
            "chart_title": chart.get("title"),
            "chart_type": chart_type,
            "interpretation": ""
        }
        
        if chart_type == "line":
            # Trend analysis
            if y_col and y_col in df.columns:
                trend = "increasing" if df[y_col].iloc[-1] > df[y_col].iloc[0] else "decreasing"
                interpretation["interpretation"] = (
                    f"This line chart shows the trend of {y_col} over time. "
                    f"The overall trend appears to be {trend}, helping identify temporal patterns and seasonality in the data."
                )
        
        elif chart_type == "bar":
            # Category comparison
            if x_col and y_col and x_col in df.columns and y_col in df.columns:
                top_category = df.groupby(x_col)[y_col].sum().idxmax()
                interpretation["interpretation"] = (
                    f"This bar chart compares {y_col} across different {x_col} categories. "
                    f"'{top_category}' shows the highest value, making it easy to identify top performers and compare relative magnitudes."
                )
        
        elif chart_type == "scatter":
            # Correlation analysis
            if x_col and y_col and x_col in df.columns and y_col in df.columns:
                corr = df[[x_col, y_col]].corr().iloc[0, 1]
                relationship = "positive" if corr > 0 else "negative"
                strength = "strong" if abs(corr) > 0.7 else "moderate" if abs(corr) > 0.4 else "weak"
                interpretation["interpretation"] = (
                    f"This scatter plot reveals the relationship between {x_col} and {y_col}. "
                    f"The data shows a {strength} {relationship} correlation (r={corr:.2f}), indicating how these variables interact."
                )
        
        elif chart_type == "heatmap":
            # Correlation matrix
            interpretation["interpretation"] = (
                f"This heatmap visualizes correlations between all numeric variables in the dataset. "
                f"Darker colors indicate stronger relationships, helping identify which variables move together or inversely."
            )
        
        interpretations.append(interpretation)
    
    return interpretations

def generate_conclusion(df, column_types, summary_stats, insights):
    """
    Generate a conclusion section summarizing the dataset.
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
    
    # Build summary
    summary_text = f"This dataset contains {len(df)} records across {len(df.columns)} columns, "
    
    if numeric_cols:
        summary_text += f"including {len(numeric_cols)} numeric variables "
    if categorical_cols:
        summary_text += f"and {len(categorical_cols)} categorical variables. "
    if datetime_cols:
        summary_text += f"Time-series data is available through {len(datetime_cols)} datetime column(s). "
    
    conclusion["summary"] = summary_text
    
    # Key findings from insights
    if insights and len(insights) > 0:
        conclusion["key_findings"] = insights[:3]  # Top 3 insights
    
    # Data characteristics
    characteristics = []
    
    # Check data completeness
    total_missing = df.isnull().sum().sum()
    if total_missing == 0:
        characteristics.append("The dataset is complete with no missing values.")
    else:
        missing_pct = (total_missing / (len(df) * len(df.columns))) * 100
        characteristics.append(f"Data completeness: {100 - missing_pct:.1f}% (minimal missing values handled through imputation).")
    
    # Check numeric ranges
    if numeric_cols:
        main_numeric = numeric_cols[0]
        if main_numeric in df.columns:
            characteristics.append(
                f"Primary numeric variable '{main_numeric}' ranges from "
                f"{df[main_numeric].min():.2f} to {df[main_numeric].max():.2f}."
            )
    
    # Check categorical diversity
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
