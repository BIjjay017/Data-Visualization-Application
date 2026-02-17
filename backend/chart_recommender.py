import pandas as pd
import numpy as np

def recommend_charts(columns, df):
    """
    Generates chart recommendations based on column types.
    columns: dict with 'numeric', 'categorical', 'datetime' keys.
    df: The dataframe to calculate bins or aggregates.
    """
    recommendations = []
    
    numeric_cols = columns.get("numeric", [])
    categorical_cols = columns.get("categorical", [])
    datetime_cols = columns.get("datetime", [])
    
    # 1. Date + Numeric -> Line Chart (Trend)
    if datetime_cols and numeric_cols:
        date_col = datetime_cols[0]
        # Sort by date for line chart
        df_sorted = df.sort_values(by=date_col)
        
        for num_col in numeric_cols:
            # We can't send all points if too many, maybe aggregate by month/year?
            # For MVP, let's strictly limit points or just send raw if < 1000.
            # But here we just return config.
            recommendations.append({
                "type": "line",
                "x": date_col,
                "y": num_col,
                "title": f"Trend of {num_col} over time"
            })
    
    # 2. Categorical + Numeric -> Aggregated Bar Chart
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0] 
        # Check cardinality
        unique_count = df[cat_col].nunique()
        
        if unique_count <= 15: # Only show if readable
            for num_col in numeric_cols:
                # Pre-aggregate
                agg_data = df.groupby(cat_col)[num_col].sum().reset_index()
                recommendations.append({
                    "type": "bar",
                    "x": cat_col,
                    "y": num_col,
                    "aggregation": "sum",
                    "title": f"Total {num_col} by {cat_col}",
                    "data": agg_data.to_dict(orient="records")
                })
        else:
            # Maybe Top 10?
            for num_col in numeric_cols:
                agg_data = df.groupby(cat_col)[num_col].sum().nlargest(10).reset_index()
                recommendations.append({
                    "type": "bar",
                    "x": cat_col,
                    "y": num_col,
                    "aggregation": "sum",
                    "title": f"Top 10 {cat_col} by Total {num_col}",
                    "data": agg_data.to_dict(orient="records")
                })
            
    # 3. Numeric + Numeric -> Scatter Plot
    if len(numeric_cols) >= 2:
        # Sample if too big?
        sample_df = df if len(df) < 500 else df.sample(500)
        recommendations.append({
            "type": "scatter",
            "x": numeric_cols[0],
            "y": numeric_cols[1],
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
            "data": sample_df[[numeric_cols[0], numeric_cols[1]]].to_dict(orient="records")
        })

    # 4. 1 Numeric -> Histogram
    for num_col in numeric_cols:
        # Calculate bins
        try:
            counts, bin_edges = np.histogram(df[num_col].dropna(), bins='auto')
            # Create data for bar chart representing histogram
            hist_data = []
            for i in range(len(counts)):
                label = f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}"
                hist_data.append({"range": label, "count": int(counts[i])})
                
            recommendations.append({
                "type": "bar", # Using bar to render histogram
                "x": "range",
                "y": "count",
                "title": f"Distribution of {num_col}",
                "data": hist_data
            })
        except:
            pass # Skip if histogram fails
        
    # 5. 1 Categorical -> Bar Chart (Count) or Pie Chart
    for cat_col in categorical_cols:
        unique_count = df[cat_col].nunique()
        
        if unique_count <= 5:
            # Pie Chart
            counts = df[cat_col].value_counts().reset_index()
            counts.columns = [cat_col, "count"]
            recommendations.append({
                "type": "pie",
                "x": cat_col,
                "y": "count",
                "title": f"Distribution of {cat_col}",
                "data": counts.to_dict(orient="records")
            })
        elif unique_count <= 15:
            # Bar Chart
            counts = df[cat_col].value_counts().reset_index()
            counts.columns = [cat_col, "count"]
            recommendations.append({
                "type": "bar",
                "x": cat_col,
                "y": "count",
                "title": f"Count of {cat_col}",
                "data": counts.to_dict(orient="records")
            })
        else:
            # Top 10 Bar Chart
            counts = df[cat_col].value_counts().head(10).reset_index()
            counts.columns = [cat_col, "count"]
            recommendations.append({
                "type": "bar",
                "x": cat_col,
                "y": "count",
                "title": f"Top 10 {cat_col}",
                "data": counts.to_dict(orient="records")
            })

    return recommendations
