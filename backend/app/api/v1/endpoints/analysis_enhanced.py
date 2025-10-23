# app/api/v1/endpoints/analysis_enhanced.py

"""
Enhanced analysis endpoints with filename support and WebSocket status updates.
Requirements: 1.5, 2.1, 2.3, 13.1, 13.3
"""

from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.analysis import DirectAnalysis
from pydantic import BaseModel, Field

router = APIRouter()


class AnalysisHistoryItem(BaseModel):
    analysis_id: str
    filename: str
    language: str
    status: str
    issues_count: int
    errors_count: int
    warnings_count: int
    created_at: datetime
    completed_at: Optional[datetime]
    batch_id: Optional[str]


class AnalysisHistoryResponse(BaseModel):
    analyses: List[AnalysisHistoryItem]
    total: int
    page: int
    page_size: int


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    progress: int
    filename: str
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


@router.get("/history", response_model=AnalysisHistoryResponse)
async def get_analysis_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    filename: Optional[str] = Query(None, description="Filter by filename"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis history with filenames for the current user.
    
    Requirements: 1.4, 2.3 - Show filenames in history
    """
    query = db.query(DirectAnalysis).filter(
        DirectAnalysis.user_id == current_user.id
    )
    
    if filename:
        query = query.filter(DirectAnalysis.filename.ilike(f"%{filename}%"))
    
    if status:
        query = query.filter(DirectAnalysis.status == status)
    
    # Get total count
    total = query.count()
    
    # Paginate
    offset = (page - 1) * page_size
    analyses = query.order_by(DirectAnalysis.created_at.desc()).offset(offset).limit(page_size).all()
    
    analyses_data = []
    for analysis in analyses:
        analyses_data.append(AnalysisHistoryItem(
            analysis_id=analysis.id,
            filename=analysis.filename or "untitled",
            language=analysis.language,
            status=analysis.status,
            issues_count=analysis.issues_count or 0,
            errors_count=analysis.errors_count or 0,
            warnings_count=analysis.warnings_count or 0,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at,
            batch_id=analysis.batch_id
        ))
    
    return AnalysisHistoryResponse(
        analyses=analyses_data,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current status of an analysis.
    
    Requirements: 13.1, 13.3 - Real-time status updates
    """
    analysis = db.query(DirectAnalysis).filter(
        DirectAnalysis.id == analysis_id,
        DirectAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Calculate progress
    progress = 0
    if analysis.status == "completed":
        progress = 100
    elif analysis.status == "processing":
        # Estimate progress based on time elapsed
        if analysis.created_at:
            elapsed = (datetime.utcnow() - analysis.created_at).total_seconds()
            # Assume average analysis takes 30 seconds
            progress = min(95, int((elapsed / 30) * 100))
    elif analysis.status == "failed":
        progress = 0
    
    return AnalysisStatusResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        progress=progress,
        filename=analysis.filename or "untitled",
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        error_message=analysis.error_message
    )


@router.websocket("/ws/{analysis_id}")
async def analysis_status_websocket(
    websocket: WebSocket,
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time analysis status updates.
    
    Requirements: 13.2 - WebSocket real-time updates
    """
    await websocket.accept()
    
    try:
        while True:
            # Query analysis status
            analysis = db.query(DirectAnalysis).filter(
                DirectAnalysis.id == analysis_id
            ).first()
            
            if not analysis:
                await websocket.send_json({
                    "error": "Analysis not found",
                    "analysis_id": analysis_id
                })
                break
            
            # Calculate progress
            progress = 0
            if analysis.status == "completed":
                progress = 100
            elif analysis.status == "processing":
                if analysis.created_at:
                    elapsed = (datetime.utcnow() - analysis.created_at).total_seconds()
                    progress = min(95, int((elapsed / 30) * 100))
            
            # Send status update
            await websocket.send_json({
                "analysis_id": analysis_id,
                "status": analysis.status,
                "progress": progress,
                "filename": analysis.filename or "untitled",
                "updated_at": datetime.utcnow().isoformat()
            })
            
            # Break if completed or failed
            if analysis.status in ["completed", "failed"]:
                break
            
            # Wait before next update
            await asyncio.sleep(2)
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "error": str(e),
                "analysis_id": analysis_id
            })
        except:
            pass
