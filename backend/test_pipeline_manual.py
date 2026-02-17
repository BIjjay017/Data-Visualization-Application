import pandas as pd
import numpy as np
from main import upload_file
import asyncio
from fastapi import UploadFile
import io

# Create a sample dataframe with various issues
df = pd.DataFrame({
    'id': range(1, 21), # Numeric but ID
    'category': ['A', 'B', 'A', 'A', 'B', 'C', None, 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'C', 'A'],
    'value': [10.12345, 20.67891, 10.1, np.nan, 20.2, 30.3, 10.4, 20.5, 30.6, 1000.0, 10.0, 20.0, 30.0, 10.0, 20.0, 30.0, 10.0, 20.0, 30.0, 10.0], # Has outlier 1000.0, missing, lots of decimals
    'date': pd.date_range(start='2023-01-01', periods=20),
    'mixed': ['1', '2', '3', '4', '5', 'X', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20'] # Mixed type, likely categorical or numeric with error
})

# Add duplicte
df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

print("Original DF shape:", df.shape)

# Convert to CSV for upload
csv_content = df.to_csv(index=False).encode('utf-8')

async def test():
    file = UploadFile(filename="test.csv", file=io.BytesIO(csv_content))
    response = await upload_file(file)
    
    if "error" in response:
        print("Error:", response["error"])
        return

    print("\n--- Cleaning Report ---")
    print(response["cleaning_report"])
    
    print("\n--- Metadata ---")
    print(response["metadata"])
    
    print("\n--- Summary ---")
    print(response["summary"])
    
    print("\n--- Recommended Charts ---")
    for chart in response["recommended_charts"]:
        print(f"Type: {chart['type']}, Title: {chart['title']}")
        
    print("\n--- Data Sample (Value column) ---")
    for row in response["data"][:5]:
        print(row.get("value"))

if __name__ == "__main__":
    asyncio.run(test())
