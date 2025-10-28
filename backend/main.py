"""
FastAPI Backend for Medical Document RAG System
Main API endpoints for document upload, chat, and report generation
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from loguru import logger

from agents.orchestrator import OrchestratorAgent
from agents.document_loader import DocumentLoaderAgent
from agents.qa_agent import QAAgent
from agents.extraction_agent import ExtractionAgent
from agents.report_agent import ReportAssemblyAgent
from services.vector_store import VectorStoreService
from services.session_manager import SessionManager

# Initialize FastAPI app
app = FastAPI(
    title="Medical Document RAG API",
    description="AI-powered assistant for healthcare document management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
vector_store = VectorStoreService()
session_manager = SessionManager()
orchestrator = OrchestratorAgent(vector_store, session_manager)

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("reports", exist_ok=True)
os.makedirs("data/chroma", exist_ok=True)

# Pydantic Models
class ChatRequest(BaseModel):
    session_id: str
    message: str
    
class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    session_id: str

class ReportRequest(BaseModel):
    session_id: str
    sections: List[str]  # e.g., ["Introduction", "Clinical Findings", "Summary"]
    
class ReportResponse(BaseModel):
    report_path: str
    session_id: str

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Medical Document RAG API",
        "version": "1.0.0"
    }

@app.post("/upload")
async def upload_documents(
    session_id: str,
    files: List[UploadFile] = File(...)
):
    """
    Upload and process multiple medical documents
    Supports: PDF, DOCX, XLSX, PNG, JPG
    """
    try:
        logger.info(f"Uploading {len(files)} files for session {session_id}")
        
        # Save uploaded files
        file_paths = []
        for file in files:
            file_path = f"uploads/{session_id}_{file.filename}"
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            file_paths.append(file_path)
        
        # Process documents through orchestrator
        result = await orchestrator.process_documents(session_id, file_paths)
        
        return {
            "status": "success",
            "session_id": session_id,
            "files_processed": len(file_paths),
            "message": result
        }
        
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for Q&A with uploaded documents
    Maintains conversation history and context
    """
    try:
        logger.info(f"Chat request for session {request.session_id}")
        
        # Check if session exists
        if not session_manager.session_exists(request.session_id):
            raise HTTPException(
                status_code=404,
                detail="Session not found. Please upload documents first."
            )
        
        # Process query through orchestrator
        response = await orchestrator.process_query(
            request.session_id,
            request.message
        )
        
        return ChatResponse(
            response=response["answer"],
            sources=response.get("sources", []),
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Generate structured medical report from uploaded documents
    Extracts tables, charts, and creates summaries
    """
    try:
        logger.info(f"Generating report for session {request.session_id}")
        
        # Check if session exists
        if not session_manager.session_exists(request.session_id):
            raise HTTPException(
                status_code=404,
                detail="Session not found. Please upload documents first."
            )
        
        # Generate report through orchestrator
        report_path = await orchestrator.generate_report(
            request.session_id,
            request.sections
        )
        
        return ReportResponse(
            report_path=report_path,
            session_id=request.session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-report/{session_id}/{filename:path}")
async def download_report(session_id: str, filename: str):
    """
    Download generated PDF report
    """
    try:
        # Securely get the base filename to prevent directory traversal
        base_filename = os.path.basename(filename)
        file_path = f"reports/{base_filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report not found")
        
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=base_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/sessions/{session_id}/history")
async def get_chat_history(session_id: str):
    """
    Retrieve chat history for a session
    """
    try:
        history = session_manager.get_history(session_id)
        return {
            "session_id": session_id,
            "history": history
        }
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete session and associated data
    """
    try:
        session_manager.delete_session(session_id)
        return {
            "status": "success",
            "message": f"Session {session_id} deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)