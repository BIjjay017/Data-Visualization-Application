import pandas as pd
import numpy as np

def clean_data(df):
    """
    Cleans the dataframe by handling missing values.
    For simplicity, we'll fill numeric NaNs with 0 and others with 'Unknown'.
    """
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna('Unknown')
    return df

def detect_columns(df):
    """
    Identifies column types: Numeric, Categorical, Datetime.
    """
    column_types = {
        "numeric": [],
        "categorical": [],
        "datetime": []
    }

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            column_types["numeric"].append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
             column_types["datetime"].append(col)
        # Check if it looks like a date string
        elif df[col].dtype == 'object':
            try:
                pd.to_datetime(df[col], errors='raise')
                # If distinct values are too many, treating as categorical might be wrong, 
                # but for this MVP, if it parses as date, we treat as date or categorical?
                # Let's try to convert and see.
                # Actually, let's keep it simple: if it converts to datetime, it's datetime.
                # But we don't want to mutate df here, just check.
                # However, to be useful, we probably should convert the DF in place or return a new one.
                # For this function, let's just categorize. 
                # But wait, main.py needs the converted DF. 
                # So we should probably have a 'preprocess_types' function.
                column_types["categorical"].append(col) # Defaulting object to categorical for now
            except:
                column_types["categorical"].append(col)
        else:
             column_types["categorical"].append(col)

    # Refine datetime detection for object columns
    # This is a bit tricky without modifying the DF. 
    # Let's assume the DF passed here has already been type-converted if possible 
    # OR we rely on main.py to do pd.read_csv(parse_dates=True) or similar.
    # For robust MVP, let's do a quick check on 'categorical' to see if they are actually dates.
    
    actual_categorical = []
    
    for col in column_types["categorical"]:
        is_date = False
        if df[col].dtype == 'object':
            try:
                # Sample check to avoid performance hit on large data
                pd.to_datetime(df[col].dropna().iloc[:10], errors='raise') 
                # If sample passes, assume it's date.
                column_types["datetime"].append(col)
                is_date = True
            except:
                pass
        
        if not is_date:
            actual_categorical.append(col)
            
    column_types["categorical"] = actual_categorical
    
    return column_types

def get_summary(df):
    """
    Returns basic summary statistics.
    """
    summary = {}
    
    # Total rows
    summary["total_rows"] = len(df)
    
    # Numeric summaries
    for col in df.select_dtypes(include=[np.number]).columns:
        summary[f"{col}_sum"] = float(df[col].sum())
        summary[f"{col}_mean"] = float(df[col].mean())
        summary[f"{col}_max"] = float(df[col].max())
        summary[f"{col}_min"] = float(df[col].min())
        
    return summary
