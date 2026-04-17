from fastapi import FastAPI, UploadFile, File, Response, Depends, Header, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import os
import secrets
import logging
import uvicorn

# Load environment variables from .env file
load_dotenv()

from file_parser import parse_file
from data_cleaner import clean_data
from data_processor import get_summary
from chart_recommender import recommend_charts
from insight_generator import generate_insights
from summary_generator import generate_dataset_summary, generate_chart_interpretations, generate_conclusion
from report_generator import generate_pdf_report, generate_seaborn_boxplot_base64
from chatbot import process_chat_message, generate_smart_suggestions
from database import init_db, SessionLocal, AnalysisResult, get_db
from sqlalchemy.orm import Session

# Initialize Database
init_db()

app = FastAPI()
logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"csv", "xls", "xlsx", "pdf", "doc", "docx"}


def _get_allowed_origins() -> List[str]:
    configured_origins = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    origins = []
    for origin in configured_origins.split(","):
        cleaned = origin.strip().rstrip("/")
        if cleaned:
            origins.append(cleaned)
    return origins


def _get_allowed_origin_regex() -> Optional[str]:
    regex = os.environ.get("ALLOWED_ORIGIN_REGEX", "").strip()
    return regex or None

def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    return obj

# In-memory session cache: session_id -> analysis payload
latest_analysis = {}

# Pydantic models for chat
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None

# CORS configuration for production and development
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_origin_regex=_get_allowed_origin_regex(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def resolve_session_id(
    x_session_id: Optional[str] = Header(default=None, alias="X-Session-Id"),
    session_id: Optional[str] = Query(default=None),
) -> str:
    resolved = x_session_id or session_id
    if not resolved:
        raise HTTPException(status_code=401, detail="Missing session ID")
    return resolved

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise ValueError("File must include a valid name")

        extension = file.filename.rsplit('.', 1)[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {extension}")

        contents = await file.read()
        if len(contents) > MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"File is too large. Maximum size is {MAX_UPLOAD_SIZE_MB}MB")
        
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
        
        # Post-process charts: Replace or augment Box Plots with Seaborn images
        for chart in charts:
            if chart.get("type") == "boxPlot":
                col = chart.get("column")
                if col:
                    img_base64 = generate_seaborn_boxplot_base64(df, col)
                    if img_base64:
                        chart["type"] = "image"
                        chart["imageData"] = img_base64
        
        # STEP 6: Insights
        generated_insights = generate_insights(df, summary)
        all_insights = generated_insights + anomalies_insights
        
        # STEP 7: Generator Wrappers (Conclusion etc)
        dataset_summary = generate_dataset_summary(df, columns)
        chart_interpretations = await generate_chart_interpretations(charts, df, columns)
        conclusion = await generate_conclusion(df, columns, summary, all_insights)

        session_id = secrets.token_urlsafe(24)
        
        result = {
            "session_id": session_id,
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

        # STEP 8: Save to Database for future reference
        try:
            db = SessionLocal()
            db_analysis = AnalysisResult(
                filename=file.filename,
                result_data=convert_numpy_types(result),
                data_preview=df.fillna("").head(20).to_dict(orient="records")
            )
            db.add(db_analysis)
            db.commit()
            db.refresh(db_analysis)
            result["id"] = db_analysis.id
            db.close()
        except Exception as db_err:
            logger.warning("Database save failed: %s", db_err)
        
        # Cache for PDF generation (store DF and COLUMNS separately to avoid serialization issues in JSON if we needed to serialize)
        # But here latest_analysis is in-memory dict, so storing DF is fine.
        latest_analysis[session_id] = {
            "result": result,
            "df": df,
            "columns": columns
        }
        
        return convert_numpy_types(result)
    
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as exc:
        logger.exception("An error occurred while processing upload")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing the file",
        ) from exc

@app.get("/history")
async def get_history(session_id: str = Depends(resolve_session_id), db: Session = Depends(get_db)):
    """List previous analyses."""
    history = db.query(AnalysisResult).order_by(AnalysisResult.upload_date.desc()).all()
    response = []
    for item in history:
        result_data = item.result_data or {}
        if isinstance(result_data, dict) and result_data.get("session_id") == session_id:
            response.append({
                "id": item.id,
                "filename": item.filename,
                "date": item.upload_date.isoformat(),
            })
    return response

@app.get("/history/{item_id}")
async def get_history_item(item_id: int, session_id: str = Depends(resolve_session_id), db: Session = Depends(get_db)):
    """Retrieve a specific analysis."""
    item = db.query(AnalysisResult).filter(AnalysisResult.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Analysis not found")

    result_data = item.result_data or {}
    if not isinstance(result_data, dict) or result_data.get("session_id") != session_id:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Update session cache for chat/download
    latest_analysis[session_id] = {
        "result": result_data,
        "df": pd.DataFrame(item.data_preview), # Limited context for chat
        "columns": result_data.get("columns", {})
    }
    
    return result_data

@app.get("/download_report")
async def download_report(session_id: str = Depends(resolve_session_id)):
    analysis = latest_analysis.get(session_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis available for this session")
    
    try:
        # Retrieve cached data
        result = analysis.get("result")
        df = analysis.get("df")
        columns = analysis.get("columns")
        
        pdf_content = generate_pdf_report(result, df, columns)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=report.pdf"}
        )
    except Exception as exc:
        logger.exception("Failed to generate report")
        raise HTTPException(status_code=500, detail="Failed to generate report") from exc


@app.post("/chat")
async def chat(request: ChatRequest, session_id: str = Depends(resolve_session_id)):
    """
    Chat endpoint for interacting with the dataset using AI.
    """
    analysis = latest_analysis.get(session_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No data available for this session")
    
    try:
        df = analysis.get("df")
        columns = analysis.get("columns")
        result = analysis.get("result", {})
        summary = result.get("summary", {})
        insights = result.get("insights", [])
        
        # Convert chat history to proper format
        history = None
        if request.history:
            history = [{"role": msg.role, "content": msg.content} for msg in request.history]
        
        # Process the message
        response = process_chat_message(
            message=request.message,
            df=df,
            columns=columns,
            summary=summary,
            insights=insights,
            chat_history=history
        )
        
        return {
            "response": response,
            "suggestions": None  # Suggestions only on initial load
        }
        
    except Exception as exc:
        logger.exception("Chat processing failed")
        raise HTTPException(status_code=500, detail="Chat request failed") from exc


@app.get("/chat/suggestions")
async def get_chat_suggestions(session_id: str = Depends(resolve_session_id)):
    """
    Get smart question suggestions based on the current dataset.
    """
    analysis = latest_analysis.get(session_id)
    if not analysis:
        return {"suggestions": [
            "Upload a file to start analyzing your data",
            "What kind of data can I analyze?",
            "How does the chatbot work?"
        ]}
    
    try:
        df = analysis.get("df")
        columns = analysis.get("columns")
        result = analysis.get("result", {})
        insights = result.get("insights", [])
        
        suggestions = generate_smart_suggestions(df, columns, insights)
        
        return {"suggestions": suggestions}
        
    except Exception:
        return {"suggestions": [
            "What patterns exist in my data?",
            "Give me a summary of this dataset",
            "What are the key insights?"
        ]}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_sessions": len(latest_analysis)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
