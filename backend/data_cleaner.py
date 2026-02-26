import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.preprocessing import LabelEncoder
from scipy import stats
import re
from datetime import datetime

def standardize_column_names(df):
    """
    Standardize column names: lowercase, replace spaces and special chars with underscores.
    """
    df_clean = df.copy()
    new_columns = {}
    for col in df.columns:
        # Convert to lowercase, replace special chars with underscore
        new_name = re.sub(r'[^\w\s]', '', str(col).lower())
        new_name = re.sub(r'\s+', '_', new_name.strip())
        # Handle duplicates
        if new_name in new_columns.values():
            suffix = 1
            while f"{new_name}_{suffix}" in new_columns.values():
                suffix += 1
            new_name = f"{new_name}_{suffix}"
        new_columns[col] = new_name
    df_clean.columns = [new_columns[col] for col in df.columns]
    return df_clean, new_columns

def trim_whitespace(df):
    """
    Trim leading/trailing whitespace from all string columns.
    """
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    return df_clean

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
        "NaN", "nan", "NAN",
        "undefined", "Undefined", "UNDEFINED",
        "#N/A", "#VALUE!", "#REF!", "#DIV/0!",
        "N.A.", "n.a.", "Not Available", "not available"
    ]
    
    df_clean = df.copy()
    
    # Efficiently replace in object columns only
    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].replace(missing_indicators, np.nan)
        
    return df_clean

def detect_and_convert_boolean(df):
    """
    Detect and convert boolean columns from string representations.
    """
    df_clean = df.copy()
    boolean_mappings = {
        'true': True, 'false': False,
        'yes': True, 'no': False,
        'y': True, 'n': False,
        '1': True, '0': False,
        't': True, 'f': False,
        'on': True, 'off': False
    }
    
    converted_cols = []
    for col in df_clean.select_dtypes(include=['object']).columns:
        non_null_vals = df_clean[col].dropna().astype(str).str.lower().unique()
        if len(non_null_vals) <= 2:
            if all(val in boolean_mappings for val in non_null_vals):
                df_clean[col] = df_clean[col].astype(str).str.lower().map(boolean_mappings)
                converted_cols.append(col)
    
    return df_clean, converted_cols

def standardize_numeric_formats(df):
    """
    Standardize numeric formats: remove currency symbols, thousand separators, percentages.
    """
    df_clean = df.copy()
    converted_cols = []
    
    for col in df_clean.select_dtypes(include=['object']).columns:
        sample = df_clean[col].dropna().head(100).astype(str)
        
        # Check for currency patterns ($1,234.56 or EUR 1.234,56)
        currency_pattern = r'^[\$€£¥₹]?\s*[\d,\.]+\s*[\$€£¥₹]?$'
        if sample.str.match(currency_pattern).mean() > 0.8:
            try:
                cleaned = df_clean[col].astype(str).str.replace(r'[\$€£¥₹,\s]', '', regex=True)
                df_clean[col] = pd.to_numeric(cleaned, errors='coerce')
                converted_cols.append((col, 'currency'))
            except:
                pass
        
        # Check for percentage patterns (45% or 45.5%)
        pct_pattern = r'^[\d\.]+\s*%$'
        if sample.str.match(pct_pattern).mean() > 0.8:
            try:
                cleaned = df_clean[col].astype(str).str.replace('%', '', regex=False).str.strip()
                df_clean[col] = pd.to_numeric(cleaned, errors='coerce') / 100
                converted_cols.append((col, 'percentage'))
            except:
                pass
    
    return df_clean, converted_cols

def coerce_data_types(df):
    """
    Intelligently coerce data types based on column content.
    """
    df_clean = df.copy()
    type_changes = {}
    
    for col in df_clean.columns:
        original_type = str(df_clean[col].dtype)
        
        # Skip if already well-typed
        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            continue
        if pd.api.types.is_bool_dtype(df_clean[col]):
            continue
            
        # Try datetime conversion for object columns
        if df_clean[col].dtype == 'object':
            try:
                sample = df_clean[col].dropna().head(50)
                if len(sample) > 0:
                    # Try multiple date formats
                    converted = pd.to_datetime(sample, errors='raise', infer_datetime_format=True)
                    df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce', infer_datetime_format=True)
                    type_changes[col] = {'from': original_type, 'to': 'datetime'}
                    continue
            except:
                pass
        
        # Try numeric conversion
        if df_clean[col].dtype == 'object':
            try:
                numeric_vals = pd.to_numeric(df_clean[col], errors='coerce')
                # Only convert if more than 80% can be converted
                if numeric_vals.notna().mean() > 0.8:
                    df_clean[col] = numeric_vals
                    type_changes[col] = {'from': original_type, 'to': str(numeric_vals.dtype)}
            except:
                pass
        
        # Convert int64 to Int64 (nullable integer) if there are NaNs
        if pd.api.types.is_float_dtype(df_clean[col]):
            # Check if values are actually integers
            non_null = df_clean[col].dropna()
            if len(non_null) > 0 and (non_null == non_null.astype(int)).all():
                df_clean[col] = df_clean[col].astype('Int64')
                type_changes[col] = {'from': original_type, 'to': 'Int64'}
    
    return df_clean, type_changes

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

def apply_imputation(df, metadata, use_knn=False):
    """
    Apply intelligent imputation based on missing percentage and column type.
    Optionally use KNN imputation for numeric columns.
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
            # Use KNN imputation for small-medium datasets if enabled
            if use_knn and len(df_clean) < 10000 and missing_pct < 30:
                try:
                    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
                    if col in numeric_cols and len(numeric_cols) > 1:
                        imputer = KNNImputer(n_neighbors=5)
                        df_clean[numeric_cols] = imputer.fit_transform(df_clean[numeric_cols])
                        strategy = "knn_imputation"
                    else:
                        raise ValueError("Fallback to median")
                except:
                    imputer = SimpleImputer(strategy='median')
                    df_clean[col] = imputer.fit_transform(df_clean[[col]]).ravel()
                    strategy = "median_imputation"
            else:
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
            # DateTime handling with intelligent fill
            try:
                df_clean[col] = pd.to_datetime(df_clean[col])
                # Try interpolation first, then forward/backward fill
                df_clean[col] = df_clean[col].interpolate(method='time', limit_direction='both')
                df_clean[col] = df_clean[col].ffill().bfill()
                strategy = "interpolation_and_fill"
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
    1. Standardize column names
    2. Trim whitespace
    3. Remove duplicates
    4. Standardize missing values
    5. Convert boolean columns
    6. Standardize numeric formats (currency, percentages)
    7. Coerce data types
    8. Calculate Metadata (Types, Missing, Skew, etc.)
    9. Apply Imputation
    10. Detect Outliers (Reporting)
    11. Round Floats
    """
    
    report = {
        "steps_executed": [],
        "metadata": {},
        "cleaning_summary": {},
        "transformations": {}
    }
    
    # 1. Standardize Column Names
    df_named, column_mapping = standardize_column_names(df)
    report["steps_executed"].append("standardize_column_names")
    report["transformations"]["column_renames"] = column_mapping
    
    # 2. Trim Whitespace
    df_trimmed = trim_whitespace(df_named)
    report["steps_executed"].append("trim_whitespace")
    
    # 3. Remove Duplicates
    df_deduped, dup_count = remove_duplicates(df_trimmed)
    report["steps_executed"].append("remove_duplicates")
    report["cleaning_summary"]["duplicates_removed"] = int(dup_count)
    
    # 4. Standardize Missing
    df_standardized = standardize_missing(df_deduped)
    report["steps_executed"].append("standardize_missing")
    
    # 5. Convert Boolean Columns
    df_bool, bool_converted = detect_and_convert_boolean(df_standardized)
    report["steps_executed"].append("convert_boolean_columns")
    report["transformations"]["boolean_columns"] = bool_converted
    
    # 6. Standardize Numeric Formats
    df_numeric, numeric_conversions = standardize_numeric_formats(df_bool)
    report["steps_executed"].append("standardize_numeric_formats")
    report["transformations"]["numeric_conversions"] = numeric_conversions
    
    # 7. Coerce Data Types
    df_typed, type_changes = coerce_data_types(df_numeric)
    report["steps_executed"].append("coerce_data_types")
    report["transformations"]["type_conversions"] = type_changes
    
    # 8. Infer Types & Metadata
    metadata = calculate_metadata(df_typed)
    report["metadata"] = metadata
    
    # 9. Handle Missing Values / Fix Data Types (Imputation)
    use_knn = len(df_typed) < 5000  # Use KNN for smaller datasets
    df_imputed, imputation_report, excluded, dropped = apply_imputation(df_typed, metadata, use_knn=use_knn)
    report["steps_executed"].append("handle_missing_values")
    report["cleaning_summary"]["imputation_details"] = imputation_report
    report["cleaning_summary"]["columns_excluded"] = excluded
    report["cleaning_summary"]["columns_dropped"] = dropped
    
    # 10. Detect Outliers (on clean data)
    outlier_info = detect_outliers_report(df_imputed, metadata)
    report["metadata"]["outliers_detected"] = outlier_info
    report["steps_executed"].append("detect_outliers")
    
    # 11. Round Floats
    df_final = round_floats(df_imputed)
    report["steps_executed"].append("round_floats")
    
    # Update metadata with final rows/cols
    report["summary"] = {
        "original_rows": len(df),
        "original_columns": len(df.columns),
        "final_rows": len(df_final),
        "final_columns": len(df_final.columns),
        "columns_imputed": len([k for k, v in imputation_report.items() if 'imputation' in str(v.get('strategy', ''))]),
        "columns_dropped": len(dropped),
        "columns_excluded": len(excluded)
    }
    
    return df_final, report

