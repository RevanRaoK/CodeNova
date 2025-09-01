# app/api/v1/endpoints/analysis.py

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db, SessionLocal
from app.services.repository_services import repository_service
from app.db import models
from pydantic import BaseModel, Field

router = APIRouter()

class AnalysisRequest(BaseModel):
    repo_id: int = Field(gt=0)
    commit_hash: str = Field(
        default="main",
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_./\-]+$",
        description="Branch name or commit hash"
    )

class AnalysisTriggerResponse(BaseModel):
    message: str
    repo_id: int
    commit_hash: str

class AnalysisSyncResponse(BaseModel):
    status: str
    repo_id: int
    commit_hash: str
    review: dict

class AnalysisRead(BaseModel):
    id: int
    repository_id: int
    commit_hash: str
    status: str
    results: Optional[dict] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Synchronous analysis function for safe BackgroundTasks usage

def run_code_analysis(repo_id: int, commit_hash: str, db: Session):
    """
    Run code analysis using the AIService and persist an Analysis row.
    """
    from app.services.ai_service import aiservice  # lazy import to avoid circulars
    try:
        # Get repository
        repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
        if not repo:
            print(f"Repository {repo_id} not found")
            return None

        print(f"Starting analysis for repo {repo_id} at commit {commit_hash}...")

        # TODO: Pull actual code from the repository at commit/branch
        sample_code = """
        def add(a, b):
            return a + b

        class Calculator:
            def multiply(self, x, y):
                return x * y
        """
        # Get code review from AIService
        review_suggestions = aiservice.get_review_for_code(sample_code)

        # Save the analysis results
        analysis = models.Analysis(
            repository_id=repo_id,
            commit_hash=commit_hash,
            status="completed",
            results={"review": review_suggestions},
            completed_at=datetime.utcnow()
        )
        db.add(analysis)
        db.commit()

        print(f"Analysis completed for repo {repo_id}")
        return review_suggestions

    except Exception as e:
        print(f"Error during analysis for repo {repo_id}: {str(e)}")
        try:
            db.rollback()
        except Exception as re:
            print(f"Rollback failed: {re}")
        try:
            analysis = models.Analysis(
                repository_id=repo_id,
                commit_hash=commit_hash,
                status="failed",
                results={"error": str(e)},
                completed_at=datetime.utcnow()
            )
            db.add(analysis)
            db.commit()
        except Exception as ie:
            print(f"Failed to persist failed analysis record: {ie}")
        raise


def run_code_analysis_background(repo_id: int, commit_hash: str):
    """Background task entrypoint: manage its own DB session."""
    db = SessionLocal()
    try:
        run_code_analysis(repo_id, commit_hash, db)
    finally:
        db.close()


@router.get("/test-gemini")
def test_gemini():
    """Quick sanity endpoint to see AIService output without DB writes."""
    from app.services.ai_service import aiservice  # local import
    sample_code = """
    def add(a, b):
        return a + b

    class Calculator:
        def multiply(self, x, y):
            return x * y
    """
    suggestions = aiservice.get_review_for_code(sample_code)
    return {"status": "success", "response": suggestions}


@router.post("/trigger-sync", response_model=AnalysisSyncResponse)
def trigger_analysis_sync(request: AnalysisRequest, db: Session = Depends(get_db)):
    """Run analysis synchronously and return the review output (for manual testing)."""
    repo = repository_service.get_repository(db, repo_id=request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    result = run_code_analysis(request.repo_id, request.commit_hash, db)
    if result is None:
        raise HTTPException(status_code=500, detail="Analysis failed to produce results")
    return {"status": "success", "repo_id": request.repo_id, "commit_hash": request.commit_hash, "review": result}


@router.post("/trigger", status_code=202, response_model=AnalysisTriggerResponse)
def trigger_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger a new code analysis for a repository.
    """
    # Verify repository exists
    repo = repository_service.get_repository(db, repo_id=request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Schedule background analysis with its own DB session
    background_tasks.add_task(run_code_analysis_background, request.repo_id, request.commit_hash)

    return {"message": f"Code analysis has been scheduled for repository {request.repo_id}.", "repo_id": request.repo_id, "commit_hash": request.commit_hash}


@router.get("/analyses/{analysis_id}", response_model=AnalysisRead)
def get_analysis_by_id(analysis_id: int = Path(gt=0), db: Session = Depends(get_db)):
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/repositories/{repo_id}/analyses", response_model=List[AnalysisRead])
def list_analyses_by_repo(
    repo_id: int = Path(gt=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    repo = repository_service.get_repository(db, repo_id=repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    q = db.query(models.Analysis).filter(models.Analysis.repository_id == repo_id).order_by(models.Analysis.created_at.desc())
    return q.offset(skip).limit(limit).all()


@router.get("/repositories/{repo_id}/analyses/latest", response_model=AnalysisRead)
def get_latest_analysis(repo_id: int = Path(gt=0), db: Session = Depends(get_db)):
    repo = repository_service.get_repository(db, repo_id=repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    analysis = (
        db.query(models.Analysis)
        .filter(models.Analysis.repository_id == repo_id)
        .order_by(models.Analysis.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="No analyses found for this repository")
    return analysis
