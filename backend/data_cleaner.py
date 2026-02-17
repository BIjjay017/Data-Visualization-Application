import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from scipy import stats

def standardize_missing(df):
    """
    Standardize all forms of missing values to NaN.
    Replaces: "", "N/A", "null", "None", "?", "missing", etc.
    """
    missing_indicators = [
        "", " ", "N/A", "n/a", "NA", "na",
        "null", "Null", "NULL",
        "None", "none", "NONE",
        "?", "??", "???",
        "missing", "Missing", "MISSING",
        "-", "--", "---",
        "NaN", "nan", "NAN"
    ]
    
    df_clean = df.copy()
    
    # Efficiently replace in object columns only
    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].replace(missing_indicators, np.nan)
        
    return df_clean

def remove_duplicates(df):
    """
    Remove duplicate rows.
    Returns: (df_clean, duplicates_count)
    """
    initial_count = len(df)
    df_clean = df.drop_duplicates()
    duplicates_count = initial_count - len(df_clean)
    return df_clean, duplicates_count

def detect_column_type(df, col):
    """
    Detect column type: numeric, categorical, datetime, or id.
    """
    # Check if already datetime
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        return "datetime"
    
    # Check if numeric
    if pd.api.types.is_numeric_dtype(df[col]):
        # Check for high cardinality (potential ID column)
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio > 0.95 and len(df) > 50: # Only treat as ID if sufficient distinct values
            return "id"
        return "numeric"
    
    # Check if object type can be converted to datetime
    if df[col].dtype == 'object':
        try:
            # Strict caching to avoid false positives on simple numbers
            if not df[col].dropna().empty:
                pd.to_datetime(df[col].dropna().iloc[:10], errors='raise')
                return "datetime"
        except:
            pass
    
    # Check for high cardinality categorical (potential ID)
    if df[col].dtype == 'object':
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio > 0.95 and len(df) > 50:
            return "id"
    
    return "categorical"

def calculate_metadata(df):
    """
    Calculate extended metadata: missing stats, skewness, cardinality, relationships.
    """
    metadata = {
        "missing_stats": {},
        "cardinality": {},
        "skewness": {},
        "relationships": {},
        "column_types": {}
    }
    
    # 1. Missing Stats & Cardinality & Column Types
    for col in df.columns:
        # Missing
        missing_percent = df[col].isnull().mean() * 100
        metadata["missing_stats"][col] = round(missing_percent, 2)
        
        # Cardinality
        metadata["cardinality"][col] = df[col].nunique()
        
        # Column Type
        metadata["column_types"][col] = detect_column_type(df, col)

    # 2. Skewness (Numeric only)
    numeric_df = df.select_dtypes(include=[np.number])
    if not numeric_df.empty:
        skewness = numeric_df.skew().to_dict()
        metadata["skewness"] = {k: round(v, 2) for k, v in skewness.items()}
        
        # 3. Relationships (Correlation)
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr().round(2)
            # Convert to a more friendly format for frontend if needed, or just dict of dicts
            # We'll use dict of dicts which JSON handles well
            metadata["relationships"] = corr_matrix.to_dict()
            
    return metadata

def apply_imputation(df, metadata):
    """
    Apply intelligent imputation based on missing percentage and column type.
    """
    df_clean = df.copy()
    imputation_report = {}
    excluded_columns = []
    dropped_columns = []
    
    missing_stats = metadata["missing_stats"]
    column_types = metadata["column_types"]
    
    for col in df.columns:
        missing_pct = missing_stats.get(col, 0)
        col_type = column_types.get(col, "categorical")
        
        # Policy: Drop if > 70% missing
        if missing_pct > 70:
            df_clean.drop(columns=[col], inplace=True)
            dropped_columns.append(col)
            imputation_report[col] = {
                "missing_percent": missing_pct,
                "strategy": "dropped",
                "reason": "More than 70% missing data"
            }
            continue
        
        # Policy: Exclude from viz if 40-70% missing
        if missing_pct > 40:
            excluded_columns.append(col)
            imputation_report[col] = {
                "missing_percent": missing_pct,
                "strategy": "excluded",
                "reason": "40-70% missing data - unreliable"
            }
            continue
        
        if missing_pct == 0:
            imputation_report[col] = {
                "missing_percent": 0,
                "strategy": "none"
            }
            continue
            
        # Imputation
        warning = missing_pct >= 10
        
        if col_type == "numeric":
            imputer = SimpleImputer(strategy='median')
            df_clean[col] = imputer.fit_transform(df_clean[[col]]).ravel()
            strategy = "median_imputation"
            
        elif col_type == "categorical":
            mode_value = df_clean[col].mode()
            if len(mode_value) > 0:
                df_clean[col].fillna(mode_value[0], inplace=True)
                strategy = f"mode_imputation ('{mode_value[0]}')"
            else:
                df_clean[col].fillna("Unknown", inplace=True)
                strategy = "filled_with_unknown"
                
        elif col_type == "datetime":
            # DateTime handling
            try:
                df_clean[col] = pd.to_datetime(df_clean[col])
                df_clean[col] = df_clean[col].ffill().bfill()
                strategy = "forward/backward_fill"
            except:
                df_clean[col].fillna("Unknown", inplace=True)
                strategy = "filled_with_unknown (conversion failed)"
                
        else:
            strategy = "no_imputation (id/other)"
            
        imputation_report[col] = {
            "missing_percent": missing_pct,
            "strategy": strategy,
            "warning": "High missing percentage" if warning else None
        }
            
    return df_clean, imputation_report, excluded_columns, dropped_columns

def detect_outliers_report(df, metadata):
    """
    Detect outliers using Z-score but do NOT remove them automatically in this function.
    Just allow the report to show them.
    (Anomaly detector module can handle more complex logic, this is for the cleaning report)
    """
    outlier_report = {}
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        return {}
        
    z_scores = np.abs(stats.zscore(numeric_df.dropna()))
    threshold = 3
    
    # We need to align z_scores with columns. stats.zscore returns numpy array
    # If there are NaNs, zscore might return NaNs. We imputed before this usually?
    # Yes, we run this on cleaned data.
    
    # If dataframe is clean (no NaNs), zscore works.
    if not numeric_df.isnull().values.any():
        outliers_mask = (z_scores > threshold)
        for idx, col in enumerate(numeric_df.columns):
            count = outliers_mask[:, idx].sum()
            if count > 0:
                outlier_report[col] = int(count)
    
    return outlier_report

def round_floats(df):
    """
    Round all float columns to 4 decimal places.
    """
    df_rounded = df.copy()
    numeric_cols = df_rounded.select_dtypes(include=['float', 'float32', 'float64']).columns
    for col in numeric_cols:
        df_rounded[col] = df_rounded[col].round(4)
    return df_rounded

def clean_data(df):
    """
    Main cleaning pipeline:
    1. Remove duplicates
    2. Standardize missing values
    3. Calculate Metadata (Types, Missing, Skew, etc.)
    4. Apply Imputation
    5. Detect Outliers (Reporting)
    6. Round Floats
    """
    
    report = {
        "steps_executed": [],
        "metadata": {},
        "cleaning_summary": {}
    }
    
    # 1. Remove Duplicates
    df_deduped, dup_count = remove_duplicates(df)
    report["steps_executed"].append("remove_duplicates")
    report["cleaning_summary"]["duplicates_removed"] = int(dup_count)
    
    # 2. Standardize Missing
    df_standardized = standardize_missing(df_deduped)
    report["steps_executed"].append("standardize_missing")
    
    # 3. Infer Types & Metadata (on standardized, pre-imputation data usually, or post? 
    # Usually we want to know what's missing before we fix it)
    metadata = calculate_metadata(df_standardized)
    report["metadata"] = metadata
    
    # 4. Handle Missing Values / Fix Data Types (Imputation)
    df_imputed, imputation_report, excluded, dropped = apply_imputation(df_standardized, metadata)
    report["steps_executed"].append("handle_missing_values")
    report["cleaning_summary"]["imputation_details"] = imputation_report
    report["cleaning_summary"]["columns_excluded"] = excluded
    report["cleaning_summary"]["columns_dropped"] = dropped
    
    # 5. Detect Outliers (on clean data)
    outlier_info = detect_outliers_report(df_imputed, metadata)
    report["metadata"]["outliers_detected"] = outlier_info # Add to metadata
    report["steps_executed"].append("detect_outliers")
    
    # 6. Round Floats
    df_final = round_floats(df_imputed)
    report["steps_executed"].append("round_floats")
    
    # Update metadata with final rows/cols
    report["summary"] = {
        "original_rows": len(df),
        "final_rows": len(df_final),
        "final_columns": len(df_final.columns)
    }
    
    return df_final, report

