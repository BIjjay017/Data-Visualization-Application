import pandas as pd
import numpy as np
from report_generator import generate_pdf_report
import os

# Create dummy data
df = pd.DataFrame({
    'A': np.random.normal(0, 1, 100),
    'B': np.random.normal(5, 2, 100),
    'C': np.random.choice(['X', 'Y', 'Z'], 100),
    'D': np.random.choice(['High', 'Low'], 100)
})

columns = {
    'numeric': ['A', 'B'],
    'categorical': ['C', 'D'],
    'datetime': []
}

analysis_results = {
    "dataset_summary": {
        "overview": {
            "total_rows": 100,
            "total_columns": 4,
            "numeric_columns": 2,
            "categorical_columns": 2
        }
    },
    "insights": ["Insight 1", "Insight 2"],
    "cleaning_report": {
        "summary": {
            "original_rows": 100,
            "cleaned_rows": 100
        }
    },
    "conclusion": {
        "summary": "This is a test conclusion."
    }
}

try:
    print("Generating PDF...")
    pdf_bytes = generate_pdf_report(analysis_results, df, columns)
    
    with open("test_report_with_charts.pdf", "wb") as f:
        f.write(pdf_bytes)
        
    print(f"PDF generated successfully. Size: {len(pdf_bytes)} bytes")
    
    # Check if temp_charts is empty (cleanup verification)
    if os.path.exists("temp_charts") and not os.listdir("temp_charts"):
        print("Cleanup successful: temp_charts is empty.")
    elif not os.path.exists("temp_charts"):
        print("Cleanup successful: temp_charts directory removed (or empty).")
    else:
        print("Warning: temp_charts not empty.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
