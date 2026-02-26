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
    
    # 1. Date + Numeric -> Line Chart (Trend) & Area Chart
    if datetime_cols and numeric_cols:
        date_col = datetime_cols[0]
        # Sort by date for line chart
        df_sorted = df.sort_values(by=date_col)
        
        for num_col in numeric_cols[:3]:  # Limit to first 3 numeric columns
            # Line chart
            chart_data = df_sorted[[date_col, num_col]].dropna().head(500)
            chart_data[date_col] = chart_data[date_col].astype(str)
            recommendations.append({
                "type": "line",
                "x": date_col,
                "y": num_col,
                "title": f"Trend of {num_col} over time",
                "data": chart_data.to_dict(orient="records")
            })
            
            # Area chart for first numeric column only
            if num_col == numeric_cols[0]:
                recommendations.append({
                    "type": "area",
                    "x": date_col,
                    "y": num_col,
                    "title": f"{num_col} Area Chart",
                    "data": chart_data.to_dict(orient="records")
                })
    
    # 2. Categorical + Numeric -> Aggregated Bar Chart & Stacked Bar
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0] 
        unique_count = df[cat_col].nunique()
        
        if unique_count <= 15:
            for num_col in numeric_cols[:2]:
                # Sum aggregation bar chart
                agg_data = df.groupby(cat_col)[num_col].sum().reset_index()
                agg_data = agg_data.sort_values(by=num_col, ascending=False)
                recommendations.append({
                    "type": "bar",
                    "x": cat_col,
                    "y": num_col,
                    "aggregation": "sum",
                    "title": f"Total {num_col} by {cat_col}",
                    "data": agg_data.to_dict(orient="records")
                })
                
                # Mean aggregation bar chart
                agg_mean = df.groupby(cat_col)[num_col].mean().reset_index()
                agg_mean[num_col] = agg_mean[num_col].round(2)
                recommendations.append({
                    "type": "bar",
                    "x": cat_col,
                    "y": num_col,
                    "aggregation": "mean",
                    "title": f"Average {num_col} by {cat_col}",
                    "data": agg_mean.to_dict(orient="records")
                })
        else:
            # Top 10 for high cardinality
            for num_col in numeric_cols[:2]:
                agg_data = df.groupby(cat_col)[num_col].sum().nlargest(10).reset_index()
                recommendations.append({
                    "type": "bar",
                    "x": cat_col,
                    "y": num_col,
                    "aggregation": "sum",
                    "title": f"Top 10 {cat_col} by Total {num_col}",
                    "data": agg_data.to_dict(orient="records")
                })
        
        # Stacked bar chart if multiple categorical columns
        if len(categorical_cols) >= 2 and numeric_cols:
            cat_col2 = categorical_cols[1]
            num_col = numeric_cols[0]
            if df[cat_col].nunique() <= 10 and df[cat_col2].nunique() <= 5:
                pivot_data = df.pivot_table(
                    values=num_col, 
                    index=cat_col, 
                    columns=cat_col2, 
                    aggfunc='sum',
                    fill_value=0
                ).reset_index()
                recommendations.append({
                    "type": "stackedBar",
                    "x": cat_col,
                    "stackKey": cat_col2,
                    "y": num_col,
                    "title": f"{num_col} by {cat_col} (stacked by {cat_col2})",
                    "data": pivot_data.to_dict(orient="records"),
                    "stackCategories": df[cat_col2].unique().tolist()[:5]
                })
            
    # 3. Numeric + Numeric -> Scatter Plot with correlation info
    if len(numeric_cols) >= 2:
        sample_df = df if len(df) < 500 else df.sample(500)
        
        # Calculate correlation
        corr = df[numeric_cols[0]].corr(df[numeric_cols[1]])
        
        recommendations.append({
            "type": "scatter",
            "x": numeric_cols[0],
            "y": numeric_cols[1],
            "title": f"{numeric_cols[0]} vs {numeric_cols[1]} (r={corr:.2f})",
            "data": sample_df[[numeric_cols[0], numeric_cols[1]]].dropna().to_dict(orient="records"),
            "correlation": round(corr, 3) if not np.isnan(corr) else None
        })
        
        # Add more scatter plots for first 3 combinations
        if len(numeric_cols) >= 3:
            corr2 = df[numeric_cols[0]].corr(df[numeric_cols[2]])
            recommendations.append({
                "type": "scatter",
                "x": numeric_cols[0],
                "y": numeric_cols[2],
                "title": f"{numeric_cols[0]} vs {numeric_cols[2]} (r={corr2:.2f})",
                "data": sample_df[[numeric_cols[0], numeric_cols[2]]].dropna().to_dict(orient="records"),
                "correlation": round(corr2, 3) if not np.isnan(corr2) else None
            })

    # 4. 1 Numeric -> Histogram with statistics
    for num_col in numeric_cols[:3]:
        try:
            col_data = df[num_col].dropna()
            counts, bin_edges = np.histogram(col_data, bins='auto')
            
            # Limit bins for readability
            if len(counts) > 20:
                counts, bin_edges = np.histogram(col_data, bins=20)
            
            hist_data = []
            for i in range(len(counts)):
                label = f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}"
                hist_data.append({"range": label, "count": int(counts[i])})
            
            # Calculate statistics
            stats = {
                "mean": round(col_data.mean(), 2),
                "median": round(col_data.median(), 2),
                "std": round(col_data.std(), 2),
                "min": round(col_data.min(), 2),
                "max": round(col_data.max(), 2)
            }
                
            recommendations.append({
                "type": "histogram",
                "x": "range",
                "y": "count",
                "column": num_col,
                "title": f"Distribution of {num_col}",
                "data": hist_data,
                "statistics": stats
            })
        except:
            pass
        
    # 5. 1 Categorical -> Pie Chart or Donut Chart or Bar Chart
    for cat_col in categorical_cols[:2]:
        unique_count = df[cat_col].nunique()
        
        if unique_count <= 5:
            # Donut Chart (better than pie for comparison)
            counts = df[cat_col].value_counts().reset_index()
            counts.columns = [cat_col, "count"]
            recommendations.append({
                "type": "donut",
                "x": cat_col,
                "y": "count",
                "title": f"Distribution of {cat_col}",
                "data": counts.to_dict(orient="records")
            })
        elif unique_count <= 10:
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
        elif unique_count <= 20:
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
            # Top 10 Horizontal Bar Chart (better for long labels)
            counts = df[cat_col].value_counts().head(10).reset_index()
            counts.columns = [cat_col, "count"]
            recommendations.append({
                "type": "horizontalBar",
                "x": "count",
                "y": cat_col,
                "title": f"Top 10 {cat_col}",
                "data": counts.to_dict(orient="records")
            })

    # 6. Correlation Heatmap (if multiple numeric columns)
    if len(numeric_cols) >= 3:
        try:
            corr_matrix = df[numeric_cols].corr().round(3)
            heatmap_data = []
            for i, row_col in enumerate(corr_matrix.index):
                for j, col_col in enumerate(corr_matrix.columns):
                    heatmap_data.append({
                        "x": col_col,
                        "y": row_col,
                        "value": corr_matrix.iloc[i, j]
                    })
            
            recommendations.append({
                "type": "heatmap",
                "title": "Correlation Matrix",
                "data": heatmap_data,
                "columns": numeric_cols
            })
        except:
            pass

    # 7. Box Plot for numeric columns (outlier visualization)
    for num_col in numeric_cols[:2]:
        try:
            col_data = df[num_col].dropna()
            q1 = col_data.quantile(0.25)
            q3 = col_data.quantile(0.75)
            median = col_data.median()
            iqr = q3 - q1
            whisker_low = max(col_data.min(), q1 - 1.5 * iqr)
            whisker_high = min(col_data.max(), q3 + 1.5 * iqr)
            outliers = col_data[(col_data < whisker_low) | (col_data > whisker_high)].tolist()[:50]
            
            recommendations.append({
                "type": "boxPlot",
                "column": num_col,
                "title": f"Box Plot of {num_col}",
                "data": [{
                    "name": num_col,
                    "min": round(whisker_low, 2),
                    "q1": round(q1, 2),
                    "median": round(median, 2),
                    "q3": round(q3, 2),
                    "max": round(whisker_high, 2),
                    "outliers": [round(o, 2) for o in outliers]
                }]
            })
        except:
            pass

    return recommendations
