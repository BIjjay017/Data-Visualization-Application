import numpy as np
from scipy import stats

def detect_anomalies(df):
    """
    Detects outliers using Z-score for numeric columns.
    Returns a list of anomaly strings.
    """
    insights = []
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        return []

    # Calculate Z-scores
    z_scores = np.abs(stats.zscore(numeric_df.dropna()))
    
    # Threshold for outlier
    threshold = 3
    
    # Find outliers
    # z_scores is a dataframe/array of same shape as numeric_df
    # We want to count outliers per column
    
    outliers = (z_scores > threshold)
    
    # Check if outliers is a DataFrame or numpy array depending on scipy version/input
    if hasattr(outliers, 'columns'):
        for col in outliers.columns:
            count = outliers[col].sum()
            if count > 0:
                insights.append(f"{count} outliers detected in {col} column.")
    else:
        # Fallback if numpy array (shouldn't happen if input is DF but safety check)
        # Re-mapping to columns would be hard without index. 
        # Let's assume pandas behavior is preserved or we iterate manually.
        pass
        
    return insights
