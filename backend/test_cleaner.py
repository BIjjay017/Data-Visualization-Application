import pandas as pd
from data_cleaner import clean_data

# Test the cleaning module
df = pd.read_csv('../messy_sales_data.csv')

print("Original Data Shape:", df.shape)
print("\nOriginal Missing Values:")
print(df.isnull().sum())

# Clean the data
cleaned_df, report = clean_data(df)

print("\n" + "="*50)
print("CLEANING REPORT SUMMARY")
print("="*50)
print(f"Original Rows: {report['summary']['original_rows']}")
print(f"Original Columns: {report['summary']['original_columns']}")
print(f"Cleaned Rows: {report['summary']['cleaned_rows']}")
print(f"Cleaned Columns: {report['summary']['cleaned_columns']}")
print(f"Columns Imputed: {report['summary']['columns_imputed']}")
print(f"Columns Dropped: {report['summary']['columns_dropped']}")
print(f"Columns Excluded from Viz: {report['summary']['columns_excluded_from_viz']}")

print("\n" + "="*50)
print("WARNINGS")
print("="*50)
for warning in report['warnings']:
    print(f"  • {warning['column']}: {warning['message']}")

print("\n" + "="*50)
print("DETAILED CLEANING ACTIONS")
print("="*50)
for col, details in report['cleaning_report'].items():
    print(f"\n{col}:")
    print(f"  Type: {details['column_type']}")
    print(f"  Missing: {details['missing_percent']}%")
    print(f"  Strategy: {details['strategy']}")
    print(f"  Action: {details['action']}")

print("\n" + "="*50)
print("CLEANED DATA SHAPE:", cleaned_df.shape)
print("Missing Values After Cleaning:")
print(cleaned_df.isnull().sum())
