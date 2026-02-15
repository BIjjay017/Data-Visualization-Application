from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import uvicorn
from file_parser import parse_file
from data_cleaner import clean_data as clean_missing_data
from data_processor import clean_data, detect_columns, get_summary
from chart_recommender import recommend_charts
from anomaly_detector import detect_anomalies
from insight_generator import generate_insights
from summary_generator import generate_dataset_summary, generate_chart_interpretations, generate_conclusion

app = FastAPI()

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
        
        # STEP 1: CLEAN MISSING DATA (NEW MODULE)
        df, cleaning_report = clean_missing_data(df_original)
        
        # STEP 2: Basic data cleaning (existing)
        df = clean_data(df)
        
        # Pre-process numeric/datetime conversions for better detection
        # Attempt to convert object columns to datetime if they look like it
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Try parsing with year first? Auto should handle YYYY-MM-DD
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass

        # STEP 3: Detect Columns (only use columns not excluded)
        excluded_cols = cleaning_report.get("excluded_columns", [])
        columns = detect_columns(df)
        
        # Filter out excluded columns from visualization
        for key in columns:
            columns[key] = [col for col in columns[key] if col not in excluded_cols]
        
        # STEP 4: Get Summary Stats
        summary = get_summary(df)
        
        # STEP 5: Anomalies
        anomalies = detect_anomalies(df)
        
        # STEP 6: Recommendations (only for non-excluded columns)
        charts = recommend_charts(columns)
        
        # STEP 7: Insights
        # Combine anomalies into insights
        generated_insights = generate_insights(df, summary)
        all_insights = generated_insights + anomalies
        
        # STEP 8: Generate detailed dataset summary (NEW)
        dataset_summary = generate_dataset_summary(df, columns)
        
        # STEP 9: Generate chart interpretations (NEW)
        chart_interpretations = generate_chart_interpretations(charts, df, columns)
        
        # STEP 10: Generate conclusion (NEW)
        conclusion = generate_conclusion(df, columns, summary, all_insights)
        
        return {
            "cleaning_report": cleaning_report,
            "dataset_summary": dataset_summary,  # NEW: Detailed dataset summary
            "columns": columns,
            "summary": summary,
            "recommended_charts": charts,
            "chart_interpretations": chart_interpretations,  # NEW: 2-line interpretations
            "insights": all_insights,
            "conclusion": conclusion,  # NEW: Conclusion section
            "data": df.fillna("").head(50).to_dict(orient="records")
        }
    
    except ValueError as ve:
        return {"error": str(ve)}
    except Exception as e:
        return {"error": f"An error occurred while processing the file: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
