from fastapi import FastAPI, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import uvicorn
from file_parser import parse_file
from data_cleaner import clean_data
from data_processor import get_summary, detect_columns
from chart_recommender import recommend_charts
from insight_generator import generate_insights
from summary_generator import generate_dataset_summary, generate_chart_interpretations, generate_conclusion
from report_generator import generate_pdf_report

app = FastAPI()

# Global storage for latest analysis (simple caching for MVP)
# In production, use Redis or a proper cache with session IDs
latest_analysis = {}

# CORS configuration for production and development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://data-visualization-application-1t87.vercel.app",  # Production Vercel
        "https://*.vercel.app"  # Any Vercel preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        
        # Parse file based on type
        df_original = parse_file(contents, file.filename)
        
        if df_original.empty:
            return {"error": "The uploaded file contains no data"}
        
        # STEP 1: COMPREHENSIVE DATA CLEANING PIPELINE
        # returns df_cleaned and a detailed report
        df, cleaning_report = clean_data(df_original)
        
        # Extract metadata from the report
        metadata = cleaning_report.get("metadata", {})
        
        # STEP 2: Detect Columns (using metadata from cleaning step for consistency)
        columns = {
            "numeric": [],
            "categorical": [],
            "datetime": []
        }
        
        column_types = metadata.get("column_types", {})
        excluded_cols = cleaning_report.get("cleaning_summary", {}).get("columns_excluded", [])
        
        # Populate columns dictionary, skipping excluded ones
        for col, col_type in column_types.items():
            if col in excluded_cols:
                continue
            
            if col_type == "numeric":
                columns["numeric"].append(col)
            elif col_type == "datetime":
                columns["datetime"].append(col)
            else: 
                columns["categorical"].append(col)

        # STEP 3: Get Summary Stats
        summary = get_summary(df)
        
        # STEP 4: Anomalies
        anomalies_insights = []
        if "outliers_detected" in metadata:
            for col, count in metadata["outliers_detected"].items():
                anomalies_insights.append(f"{count} outliers detected in {col}.")
        
        # STEP 5: Recommendations
        # PASS DF NOW
        charts = recommend_charts(columns, df)
        
        # STEP 6: Insights
        generated_insights = generate_insights(df, summary)
        all_insights = generated_insights + anomalies_insights
        
        # STEP 7: Generator Wrappers (Conclusion etc)
        dataset_summary = generate_dataset_summary(df, columns)
        chart_interpretations = generate_chart_interpretations(charts, df, columns)
        conclusion = generate_conclusion(df, columns, summary, all_insights)
        
        result = {
            "cleaning_report": cleaning_report,
            "metadata": metadata, # Contains skewness, cardinality, relationships, column_types
            "dataset_summary": dataset_summary,
            "columns": columns,
            "summary": summary,
            "recommended_charts": charts,
            "chart_interpretations": chart_interpretations,
            "insights": all_insights,
            "conclusion": conclusion,
            "data": df.fillna("").head(50).to_dict(orient="records")
        }
        
        # Cache for PDF generation (store DF and COLUMNS separately to avoid serialization issues in JSON if we needed to serialize)
        # But here latest_analysis is in-memory dict, so storing DF is fine.
        global latest_analysis
        latest_analysis = {
            "result": result,
            "df": df,
            "columns": columns
        }
        
        return result
    
    except ValueError as ve:
        return {"error": str(ve)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"An error occurred while processing the file: {str(e)}"}

@app.get("/download_report")
async def download_report():
    if not latest_analysis:
        return {"error": "No analysis available. Please upload a file first."}
    
    try:
        # Retrieve cached data
        result = latest_analysis.get("result")
        df = latest_analysis.get("df")
        columns = latest_analysis.get("columns")
        
        pdf_content = generate_pdf_report(result, df, columns)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=report.pdf"}
        )
    except Exception as e:
         import traceback
         traceback.print_exc()
         return {"error": f"Failed to generate report: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
