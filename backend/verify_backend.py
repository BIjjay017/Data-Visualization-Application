import pandas as pd
import numpy as np
import asyncio
import time
from main import upload_file
from database import SessionLocal, AnalysisResult, init_db
from fastapi import UploadFile
import io
import os

# Set dummy API key for testing if not present
if not os.environ.get("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = "gsk_test_key"

async def test_verification():
    # Initialize DB
    init_db()
    
    # Create sample data
    df = pd.DataFrame({
        'val': [1, 2, 3, 4, 5, 100], # Numeric with potential outlier
        'cat': ['A', 'B', 'A', 'B', 'A', 'C']
    })
    csv_content = df.to_csv(index=False).encode('utf-8')
    
    file = UploadFile(filename="verify_test.csv", file=io.BytesIO(csv_content))
    
    print("Starting processing...")
    start_time = time.time()
    
    # This will trigger 1 conclusion + 2 chart interprets (Histogram + Pie/Box)
    # Total 3 LLM calls. In parallel it should take ~ as long as 1.
    response = await upload_file(file)
    
    duration = time.time() - start_time
    print(f"Processing took: {duration:.2f} seconds")
    
    if "error" in response:
        print(f"Error: {response['error']}")
        # Note: it might error if the key is invalid, which is expected for local test
        return

    # Check database
    db = SessionLocal()
    last_analysis = db.query(AnalysisResult).order_by(AnalysisResult.id.desc()).first()
    
    if last_analysis:
        print(f"Successfully saved to DB! ID: {last_analysis.id}, Filename: {last_analysis.filename}")
        print(f"Data preview size: {len(last_analysis.data_preview)} rows")
    else:
        print("FAILED to save to database")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(test_verification())
