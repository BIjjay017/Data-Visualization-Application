import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer

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
    df_clean.replace(missing_indicators, np.nan, inplace=True)
    
    return df_clean

def calculate_missing_stats(df):
    """
    Calculate missing percentage for each column.
    Returns dict: {column_name: missing_percentage}
    """
    missing_stats = {}
    
    for col in df.columns:
        missing_percent = df[col].isnull().mean() * 100
        missing_stats[col] = round(missing_percent, 2)
    
    return missing_stats

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
        if unique_ratio > 0.95:
            return "id"
        return "numeric"
    
    # Check if object type can be converted to datetime
    if df[col].dtype == 'object':
        try:
            pd.to_datetime(df[col].dropna().iloc[:10], errors='raise')
            return "datetime"
        except:
            pass
    
    # Check for high cardinality categorical (potential ID)
    if df[col].dtype == 'object':
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio > 0.95:
            return "id"
    
    return "categorical"

def apply_imputation(df, missing_stats):
    """
    Apply intelligent imputation based on missing percentage and column type.
    
    Policy:
    - < 10%: Auto-impute
    - 10-40%: Impute with warning
    - 40-70%: Exclude from visualization
    - > 70%: Drop column
    
    Returns: (cleaned_df, imputation_report, excluded_columns, dropped_columns)
    """
    df_clean = df.copy()
    imputation_report = {}
    excluded_columns = []
    dropped_columns = []
    
    for col in df.columns:
        missing_pct = missing_stats[col]
        col_type = detect_column_type(df, col)
        
        # Policy: Drop if > 70% missing
        if missing_pct > 70:
            df_clean.drop(columns=[col], inplace=True)
            dropped_columns.append(col)
            imputation_report[col] = {
                "missing_percent": missing_pct,
                "column_type": col_type,
                "strategy": "dropped",
                "action": "column_removed",
                "reason": "More than 70% missing data"
            }
            continue
        
        # Policy: Exclude from viz if 40-70% missing
        if missing_pct > 40:
            excluded_columns.append(col)
            imputation_report[col] = {
                "missing_percent": missing_pct,
                "column_type": col_type,
                "strategy": "excluded",
                "action": "excluded_from_visualization",
                "reason": "40-70% missing data - too unreliable for visualization"
            }
            continue
        
        # No missing data
        if missing_pct == 0:
            imputation_report[col] = {
                "missing_percent": 0,
                "column_type": col_type,
                "strategy": "none",
                "action": "no_action_needed"
            }
            continue
        
        # Apply imputation based on type
        warning = missing_pct >= 10
        
        if col_type == "numeric":
            # Use median imputation
            imputer = SimpleImputer(strategy='median')
            df_clean[col] = imputer.fit_transform(df_clean[[col]]).ravel()
            
            imputation_report[col] = {
                "missing_percent": missing_pct,
                "column_type": col_type,
                "strategy": "median_imputation",
                "action": "imputed",
                "warning": "High missing percentage" if warning else None
            }
        
        elif col_type == "categorical":
            # Use mode imputation or "Unknown"
            mode_value = df_clean[col].mode()
            
            if len(mode_value) > 0:
                df_clean[col].fillna(mode_value[0], inplace=True)
                strategy = f"mode_imputation (filled with '{mode_value[0]}')"
            else:
                df_clean[col].fillna("Unknown", inplace=True)
                strategy = "filled_with_unknown"
            
            imputation_report[col] = {
                "missing_percent": missing_pct,
                "column_type": col_type,
                "strategy": strategy,
                "action": "imputed",
                "warning": "High missing percentage" if warning else None
            }
        
        elif col_type == "datetime":
            # Try to convert to datetime first
            try:
                df_clean[col] = pd.to_datetime(df_clean[col])
                # Use forward fill
                df_clean[col] = df_clean[col].ffill()
                # If still has NaN (at the beginning), use backfill
                df_clean[col] = df_clean[col].bfill()
                
                imputation_report[col] = {
                    "missing_percent": missing_pct,
                    "column_type": col_type,
                    "strategy": "forward_fill",
                    "action": "imputed",
                    "warning": "High missing percentage" if warning else None
                }
            except:
                # If conversion fails, treat as categorical
                df_clean[col].fillna("Unknown", inplace=True)
                imputation_report[col] = {
                    "missing_percent": missing_pct,
                    "column_type": "categorical",
                    "strategy": "filled_with_unknown",
                    "action": "imputed",
                    "warning": "Datetime conversion failed, treated as categorical"
                }
        
        elif col_type == "id":
            # ID columns - don't impute, just mark
            imputation_report[col] = {
                "missing_percent": missing_pct,
                "column_type": col_type,
                "strategy": "no_imputation",
                "action": "kept_as_is",
                "reason": "ID column - imputation not meaningful"
            }
    
    return df_clean, imputation_report, excluded_columns, dropped_columns

def generate_report(original_df, cleaned_df, imputation_report, excluded_columns, dropped_columns):
    """
    Generate comprehensive cleaning report.
    """
    report = {
        "summary": {
            "original_rows": len(original_df),
            "original_columns": len(original_df.columns),
            "cleaned_rows": len(cleaned_df),
            "cleaned_columns": len(cleaned_df.columns),
            "columns_dropped": len(dropped_columns),
            "columns_excluded_from_viz": len(excluded_columns),
            "columns_imputed": sum(1 for v in imputation_report.values() if v.get("action") == "imputed")
        },
        "cleaning_report": imputation_report,
        "excluded_columns": excluded_columns,
        "dropped_columns": dropped_columns,
        "warnings": [
            {
                "column": col,
                "message": details.get("warning") or details.get("reason")
            }
            for col, details in imputation_report.items()
            if details.get("warning") or (details.get("action") in ["excluded_from_visualization", "column_removed"])
        ]
    }
    
    return report

def clean_data(df):
    """
    Main cleaning pipeline.
    
    Returns: (cleaned_df, cleaning_report)
    """
    # Step 1: Standardize missing values
    df_standardized = standardize_missing(df)
    
    # Step 2: Calculate missing stats
    missing_stats = calculate_missing_stats(df_standardized)
    
    # Step 3: Apply imputation
    df_cleaned, imputation_report, excluded_columns, dropped_columns = apply_imputation(
        df_standardized, missing_stats
    )
    
    # Step 4: Generate report
    cleaning_report = generate_report(
        df, df_cleaned, imputation_report, excluded_columns, dropped_columns
    )
    
    return df_cleaned, cleaning_report
