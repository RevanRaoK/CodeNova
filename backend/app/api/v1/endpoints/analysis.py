# app/api/v1/endpoints/analysis.py

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid
import logging

from app.core.database import get_db, SessionLocal
from app.services.repository_services import repository_service
from app.db import models
from app.models.analysis import DirectAnalysis
from app.models.file_batch import FileBatch
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.users import User
from app.schemas.analysis import (
    DirectAnalysisResponse, CodeIssue, CodeMetrics, AnalysisStatus,
    DirectAnalysisHistoryItem, AnalysisHistoryResponse, AnalysisStatsResponse
)
from pydantic import BaseModel, Field, validator

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cache to prevent duplicate analysis requests
_active_analyses = {}  # {user_id: {code_hash: analysis_id}}

class DirectCodeAnalysisRequest(BaseModel):
    code: str = Field(
        min_length=1, 
        max_length=100000, 
        description="Code content to analyze (max 100KB)"
    )
    language: str = Field(
        default="javascript", 
        description="Programming language",
        pattern=r"^[a-zA-Z0-9_+-]+$"
    )
    filename: str = Field(
        min_length=1,
        max_length=255,
        description="Filename for the code (required for tracking and history)"
    )
    
    @validator('code')
    def validate_code_content(cls, v):
        if not v.strip():
            raise ValueError('Code content cannot be empty or only whitespace')
        # Check for reasonable line count (max 2000 lines)
        lines = v.split('\n')
        if len(lines) > 2000:
            raise ValueError('Code content exceeds maximum line limit of 2000 lines')
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('Filename is required and cannot be empty')
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in v for char in invalid_chars):
            raise ValueError('Filename contains invalid characters')
        return v.strip()
    
    @validator('language')
    def validate_language(cls, v):
        supported_languages = {
            'javascript', 'typescript', 'python', 'java', 'cpp', 'c', 'csharp',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'html',
            'css', 'sql', 'json', 'yaml', 'xml', 'markdown', 'shell', 'bash'
        }
        if v.lower() not in supported_languages:
            raise ValueError(f'Unsupported language: {v}. Supported languages: {", ".join(supported_languages)}')
        return v.lower()

class CodeIssue(BaseModel):
    id: str
    line: int = Field(ge=1, description="Line number where issue occurs")
    column: int = Field(ge=1, default=1, description="Column number where issue occurs")
    severity: str = Field(description="Issue severity: error, warning, info, suggestion")
    message: str = Field(min_length=1, description="Issue description")
    rule: str = Field(description="Rule or check that triggered this issue")
    category: str = Field(default="ai-review", description="Issue category")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix or improvement")

class CodeMetrics(BaseModel):
    lines_of_code: int = Field(ge=0, description="Total lines of code")
    complexity: int = Field(ge=0, default=0, description="Cyclomatic complexity")
    maintainability_index: int = Field(ge=0, le=100, default=0, description="Maintainability index (0-100)")
    duplicate_lines: int = Field(ge=0, default=0, description="Number of duplicate lines")
    test_coverage: Optional[float] = Field(ge=0, le=100, default=None, description="Test coverage percentage")

class DirectCodeAnalysisResponse(BaseModel):
    analysis_id: str = Field(description="Unique identifier for this analysis")
    status: str = Field(description="Analysis status: pending, completed, failed")
    issues: List[CodeIssue] = Field(description="List of code issues found")
    metrics: CodeMetrics = Field(description="Code quality metrics")
    summary: str = Field(description="Analysis summary")
    created_at: datetime = Field(description="When the analysis was created")
    completed_at: Optional[datetime] = Field(default=None, description="When the analysis was completed")

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


@router.post("/analyze-code")
async def analyze_code_direct(
    request: DirectCodeAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze code directly using Gemini AI with enhanced validation and error handling.
    This endpoint is used by the frontend CodeReview page for direct code analysis.
    
    Enhanced with AST parsing and issue ID generation for feedback pipeline.
    
    Requirements covered: 1.1, 1.2, 2.1, 2.3
    """
    from app.services.ai_service import get_ai_service_for_user  # local import
    from app.utils.ast_parser import ASTParser
    from app.services.issue_id_service import IssueIDService
    
    # Generate code hash for deduplication
    import hashlib
    code_hash = hashlib.sha256(request.code.encode('utf-8')).hexdigest()[:16]
    
    # Check if this exact code is already being analyzed by this user
    if current_user.id in _active_analyses:
        if code_hash in _active_analyses[current_user.id]:
            existing_analysis_id = _active_analyses[current_user.id][code_hash]
            print(f"Duplicate analysis request detected for user {current_user.id}, returning existing analysis {existing_analysis_id}")
            raise HTTPException(
                status_code=409,
                detail=f"Analysis already in progress for this code. Analysis ID: {existing_analysis_id}"
            )
    
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    
    # Mark this analysis as active
    if current_user.id not in _active_analyses:
        _active_analyses[current_user.id] = {}
    _active_analyses[current_user.id][code_hash] = analysis_id
    
    print(f"Starting analysis for user {current_user.id}, analysis_id: {analysis_id}")
    
    # Initialize AST parser and issue ID service
    ast_parser = ASTParser()
    issue_id_service = IssueIDService()
    
    try:
        # Validate request size (additional check beyond Pydantic)
        code_size_kb = len(request.code.encode('utf-8')) / 1024
        if code_size_kb > 100:  # 100KB limit
            raise HTTPException(
                status_code=413,
                detail=f"Code content too large: {code_size_kb:.1f}KB. Maximum allowed: 100KB"
            )
        
        # Parse code using AST parser
        print("Parsing code with AST parser...")
        ast_start_time = datetime.utcnow()
        ast_result = ast_parser.parse_code(request.code, request.language)
        ast_end_time = datetime.utcnow()
        ast_processing_time = (ast_end_time - ast_start_time).total_seconds()
        
        print(f"AST parsing completed in {ast_processing_time:.3f}s, valid: {ast_result.is_valid}")
        
        # Generate code hash for issue ID generation
        code_hash = issue_id_service.generate_code_hash(request.code)
        
        # Get AI service configured with user's API key if available
        print("Getting AI service for user...")
        ai_service = get_ai_service_for_user(current_user.id, db)
        
        # Get code review suggestions from Gemini AI
        print("Calling AI service...")
        suggestions = ai_service.get_review_for_code(request.code)
        print(f"AI service returned {len(suggestions)} suggestions")
        
        # Transform suggestions to structured issue dictionaries with unique IDs
        issues = []
        issue_ids = []
        
        for i, suggestion in enumerate(suggestions):
            # Map AI service severities to frontend-expected severities
            ai_severity = suggestion.get('severity', 'info').lower()
            severity_mapping = {
                'info': 'info',
                'suggestion': 'info',
                'low': 'info',
                'medium': 'warning',
                'high': 'error',
                'critical': 'error',
                'warning': 'warning',
                'error': 'error'
            }
            severity = severity_mapping.get(ai_severity, 'info')
            
            # Generate unique issue ID based on code content and suggestion
            line_number = max(1, suggestion.get('line_number', 1))
            location = {
                'line': line_number,
                'column': 1,
                'analysis_id': analysis_id
            }
            
            # Create pattern identifier from suggestion content
            pattern = f"{severity}:{suggestion.get('comment', 'unknown')[:50]}"
            
            # Generate deterministic issue ID
            issue_id = issue_id_service.generate_issue_id(code_hash, pattern, location)
            issue_ids.append(issue_id)
            
            issue = {
                "id": issue_id,  # Use generated issue ID instead of sequential
                "line": line_number,
                "column": 1,  # Default column, could be enhanced with AST data
                "severity": severity,
                "message": suggestion.get('comment', 'No comment provided'),
                "rule": "gemini-ai-review",
                "category": "ai-review",
                "suggestion": suggestion.get("suggestion", suggestion.get("comment", ""))
            }
            issues.append(issue)
            
            # Track issue in service
            issue_id_service.track_issue_resolution(issue_id, 'open')
        
        # Calculate enhanced metrics
        lines = request.code.split('\n')
        lines_of_code = len([line for line in lines if line.strip()])  # Non-empty lines
        total_lines = len(lines)
        
        # Basic complexity calculation (could be enhanced with AST parsing)
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'catch', 'switch', 'case']
        complexity = sum(request.code.lower().count(keyword) for keyword in complexity_keywords)
        
        # Simple maintainability index calculation
        avg_line_length = sum(len(line) for line in lines) / max(1, total_lines)
        maintainability_index = max(0, min(100, 100 - (complexity * 2) - (avg_line_length / 10)))
        
        metrics = {
            "lines_of_code": lines_of_code,
            "total_lines": total_lines,
            "complexity": complexity,
            "maintainability_index": int(maintainability_index),
            "duplicate_lines": 0,  # Could be enhanced with duplicate detection
            "test_coverage": None,  # Not applicable for direct code analysis
            "comment_lines": 0,
            "blank_lines": total_lines - lines_of_code,
            "function_count": 0,
            "class_count": 0,
            "comment_ratio": 0.0,
            "complexity_per_function": None
        }
        
        # Generate comprehensive summary
        issue_count = len(issues)
        severity_counts = {}
        for issue in issues:
            severity = issue.get('severity', 'info')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary_parts = [f"Analyzed {lines_of_code} lines of {request.language} code"]
        
        if issue_count > 0:
            summary_parts.append(f"Found {issue_count} issues")
            if severity_counts:
                severity_details = []
                for severity in ['error', 'warning', 'info', 'suggestion']:
                    if severity in severity_counts:
                        severity_details.append(f"{severity_counts[severity]} {severity}{'s' if severity_counts[severity] > 1 else ''}")
                if severity_details:
                    summary_parts.append(f"({', '.join(severity_details)})")
        else:
            summary_parts.append("No issues found")
        
        summary_parts.append(f"Complexity score: {complexity}")
        summary_parts.append(f"Maintainability: {int(maintainability_index)}%")
        
        summary = ". ".join(summary_parts) + "."
        
        completed_at = datetime.utcnow()
        processing_time_ms = int((completed_at - created_at).total_seconds() * 1000)
        
        # Store analysis results in database for history tracking
        print("Storing analysis results in database...")
        try:
            # Count issues by severity for database storage
            errors_count = sum(1 for issue in issues if issue.get('severity') == 'error')
            warnings_count = sum(1 for issue in issues if issue.get('severity') == 'warning')
            
            # Prepare AST metadata for storage
            ast_metadata = None
            code_patterns = None
            
            if ast_result.is_valid:
                # Convert AST result to JSON-serializable format
                ast_metadata = {
                    'language': ast_result.language.value,
                    'is_valid': ast_result.is_valid,
                    'metadata': ast_result.metadata,
                    'pattern_count': len(ast_result.patterns),
                    'processing_time': ast_processing_time
                }
                
                # Convert patterns to JSON-serializable format
                code_patterns = []
                for pattern in ast_result.patterns:
                    pattern_dict = {
                        'pattern_type': pattern.pattern_type.value,
                        'name': pattern.name,
                        'location': {
                            'line': pattern.location.line,
                            'column': pattern.location.column,
                            'end_line': pattern.location.end_line,
                            'end_column': pattern.location.end_column
                        },
                        'context': pattern.context,
                        'complexity_score': pattern.complexity_score
                    }
                    code_patterns.append(pattern_dict)
            else:
                # Store error information if AST parsing failed
                ast_metadata = {
                    'language': ast_result.language.value,
                    'is_valid': False,
                    'error_message': ast_result.error_message,
                    'processing_time': ast_processing_time
                }
                code_patterns = []
            
            # Create database record with AST fields
            db_analysis = DirectAnalysis(
                id=analysis_id,
                user_id=current_user.id,
                code_content=request.code,
                language=request.language,
                filename=request.filename,
                status="completed",
                created_at=created_at,
                completed_at=completed_at,
                results={
                    "issues": issues,
                    "metrics": metrics,
                    "summary": summary,
                    "processing_time_ms": processing_time_ms,
                    "ai_model_used": "gemini-ai"
                },
                lines_of_code=metrics["lines_of_code"],
                complexity_score=metrics["complexity"],
                maintainability_index=metrics["maintainability_index"],
                issues_count=len(issues),
                errors_count=errors_count,
                warnings_count=warnings_count,
                file_size_bytes=len(request.code.encode('utf-8')),
                # New AST-related fields
                ast_metadata=ast_metadata,
                code_patterns=code_patterns,
                issue_ids=issue_ids,
                ast_processing_time=ast_processing_time
            )
            
            db.add(db_analysis)
            
            # Create Issue records for each detected issue
            from app.models.feedback import Issue
            
            for issue_data in issues:
                # Get issue_id from either "issue_id" or "id" field
                issue_id = issue_data.get("issue_id") or issue_data.get("id")
                if not issue_id:
                    print(f"Warning: Issue data missing issue_id: {issue_data}")
                    continue
                    
                db_issue = Issue(
                    id=issue_id,
                    analysis_id=analysis_id,
                    pattern_type=issue_data.get("rule", "unknown"),
                    severity=issue_data["severity"],
                    category=issue_data.get("category", "ai-review"),
                    location={
                        "line": issue_data["line"],
                        "column": issue_data["column"],
                        "context": issue_data.get("suggestion", "")[:100]
                    },
                    suggestion_text=issue_data["message"],
                    code_context=request.code[max(0, (issue_data["line"]-3)*50):(issue_data["line"]+3)*50],
                    original_code="",  # Could be enhanced to extract specific problematic code
                    suggested_fix=issue_data.get("suggestion", ""),
                    ast_node_type=None,  # Could be enhanced with AST data
                    ast_metadata=None,
                    status="active",
                    confidence_score=0.8  # Default confidence, could be enhanced
                )
                db.add(db_issue)
            
            db.commit()
            print(f"Analysis results and {len(issues)} issues stored successfully!")
            
        except Exception as db_error:
            # Log database error but don't fail the analysis
            print(f"Warning: Failed to store analysis results in database: {str(db_error)}")
            import traceback
            traceback.print_exc()
            db.rollback()
        finally:
            # Remove from active analyses
            if current_user.id in _active_analyses and code_hash in _active_analyses[current_user.id]:
                del _active_analyses[current_user.id][code_hash]
                if not _active_analyses[current_user.id]:
                    del _active_analyses[current_user.id]
        
        # Enhanced response with feedback collection interface
        response = {
            "analysis_id": analysis_id,
            "status": "completed",
            "issues": issues,
            "metrics": metrics,
            "summary": summary,
            "created_at": created_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "language": request.language,
            "filename": request.filename,
            "file_size_bytes": len(request.code.encode('utf-8')),
            "processing_time_ms": processing_time_ms,
            "ai_model_used": "gemini-ai",
            # Feedback collection interface
            "feedback_interface": {
                "enabled": True,
                "feedback_endpoint": f"/api/v1/feedback",
                "issue_retrieval_endpoint": f"/api/v1/issues",
                "analysis_issues_endpoint": f"/api/v1/analyses/{analysis_id}/issues",
                "supported_feedback_types": ["accept", "reject", "modify"],
                "feedback_instructions": {
                    "accept": "Mark this suggestion as helpful and accurate",
                    "reject": "Mark this suggestion as unhelpful or incorrect", 
                    "modify": "Provide an improved version of this suggestion"
                }
            },
            # AST processing information
            "ast_processing": {
                "enabled": ast_result.is_valid if 'ast_result' in locals() else False,
                "processing_time_seconds": ast_processing_time if 'ast_processing_time' in locals() else None,
                "patterns_detected": len(code_patterns) if code_patterns else 0,
                "language_supported": request.language in ['python', 'javascript', 'typescript']
            }
        }
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 413 for file too large)
        raise
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Remove from active analyses on error
        if current_user.id in _active_analyses and code_hash in _active_analyses[current_user.id]:
            del _active_analyses[current_user.id][code_hash]
            if not _active_analyses[current_user.id]:
                del _active_analyses[current_user.id]
        
        # Store failed analysis in database
        try:
            failed_analysis = DirectAnalysis(
                id=analysis_id,
                user_id=current_user.id,
                code_content=request.code,
                language=request.language,
                filename=request.filename,
                status="failed",
                created_at=created_at,
                completed_at=datetime.utcnow(),
                error_message=str(e),
                file_size_bytes=len(request.code.encode('utf-8')),
                lines_of_code=len(request.code.split('\n')),
                issues_count=0,
                errors_count=0,
                warnings_count=0,
                # Initialize AST fields as empty for failed analysis
                ast_metadata=None,
                code_patterns=None,
                issue_ids=None,
                ast_processing_time=None
            )
            db.add(failed_analysis)
            db.commit()
        except Exception as db_error:
            print(f"Failed to store failed analysis: {str(db_error)}")
            db.rollback()
        
        # Handle unexpected errors
        import traceback
        print(f"Error analyzing code for user {current_user.id}: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Code analysis failed: {str(e)}"
        )


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

# New endpoints for direct analysis management

# Moved the /direct/{analysis_id} route to the end to avoid conflicts

@router.get("/direct/test")
def test_direct_endpoint():
    """Simple test endpoint to verify routing works"""
    return {"message": "Direct endpoint routing works!"}

@router.get("/direct/history", status_code=200)
async def get_analysis_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    language: Optional[str] = Query(default=None, description="Filter by programming language"),
    status: Optional[str] = Query(default=None, description="Filter by analysis status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's analysis history including both direct and repository analyses.
    
    Requirements covered: 2.1, 5.1, 5.2
    """
    print(f"DEBUG: get_analysis_history called for user {current_user.id}")
    try:
        # Get direct analyses
        print(f"DEBUG: Building query for user_id {current_user.id}")
        direct_query = db.query(DirectAnalysis).filter(DirectAnalysis.user_id == current_user.id)
        
        # Apply filters for direct analyses
        if language:
            print(f"DEBUG: Filtering by language: {language}")
            direct_query = direct_query.filter(DirectAnalysis.language == language.lower())
        if status:
            print(f"DEBUG: Filtering by status: {status}")
            direct_query = direct_query.filter(DirectAnalysis.status == status.lower())
        
        direct_analyses = direct_query.order_by(DirectAnalysis.created_at.desc()).all()
        
        # Get repository analyses
        from app.models.github_integration import PRAnalysis, GitHubRepository
        repo_query = db.query(PRAnalysis).join(
            GitHubRepository, PRAnalysis.repository_id == GitHubRepository.id
        ).filter(GitHubRepository.user_id == current_user.id)
        
        repo_analyses = repo_query.order_by(PRAnalysis.created_at.desc()).all()
        
        # Get batch analyses
        from app.models.file_batch import BatchFile, FileStatus
        batch_query = db.query(BatchFile).join(
            FileBatch, BatchFile.batch_id == FileBatch.id
        ).filter(
            FileBatch.user_id == current_user.id,
            BatchFile.status == FileStatus.COMPLETED
        )
        
        # Apply filters for batch analyses
        if language:
            batch_query = batch_query.filter(BatchFile.language == language.lower())
        
        batch_files = batch_query.order_by(BatchFile.completed_at.desc()).all()
        
        # Combine and sort all analyses
        all_analyses = []
        
        # Add direct analyses
        for analysis in direct_analyses:
            all_analyses.append({
                "analysis_id": str(analysis.id),
                "id": str(analysis.id),
                "type": "direct",
                "status": str(analysis.status),
                "language": (analysis.language or "unknown"),
                "filename": analysis.filename or f"code.{analysis.language or 'txt'}",
                "issues_count": analysis.issues_count or 0,
                "issuesCount": analysis.issues_count or 0,
                "errors_count": analysis.errors_count or 0,
                "errorsCount": analysis.errors_count or 0,
                "warnings_count": analysis.warnings_count or 0,
                "warningsCount": analysis.warnings_count or 0,
                "lines_of_code": analysis.lines_of_code or 0,
                "linesOfCode": analysis.lines_of_code or 0,
                "created_at": analysis.created_at.isoformat(),
                "createdAt": analysis.created_at.isoformat(),
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                "completedAt": analysis.completed_at.isoformat() if analysis.completed_at else None
            })
        
        # Add repository analyses
        for analysis in repo_analyses:
            repo = db.query(GitHubRepository).filter(GitHubRepository.id == analysis.repository_id).first()
            formatted_status = analysis.status.value if hasattr(analysis.status, 'value') else str(analysis.status)
            lines_of_code = getattr(analysis, "lines_of_code", None) or 0
            all_analyses.append({
                "analysis_id": str(analysis.id),
                "id": str(analysis.id),
                "type": "repository",
                "status": formatted_status,
                "language": "multiple",
                "filename": f"Full Repository Analysis - {repo.repo_name if repo else 'Unknown'}",
                "repository_name": repo.repo_name if repo else "Unknown",
                "repositoryName": repo.repo_name if repo else "Unknown",
                "issues_count": analysis.issues_found or 0,
                "issuesCount": analysis.issues_found or 0,
                "errors_count": analysis.errors_count or 0,
                "errorsCount": analysis.errors_count or 0,
                "warnings_count": analysis.warnings_count or 0,
                "warningsCount": analysis.warnings_count or 0,
                "lines_of_code": lines_of_code,
                "linesOfCode": lines_of_code,
                "created_at": analysis.created_at.isoformat(),
                "createdAt": analysis.created_at.isoformat(),
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                "completedAt": analysis.completed_at.isoformat() if analysis.completed_at else None
            })
        
        # Add batch analyses
        for batch_file in batch_files:
            lines_count = len(batch_file.file_content.split('\n')) if batch_file.file_content else 0
            all_analyses.append({
                "analysis_id": str(batch_file.id),
                "id": str(batch_file.id),
                "type": "batch",
                "status": "completed",
                "language": batch_file.language or "unknown",
                "filename": batch_file.filename,
                "batch_id": batch_file.batch_id,
                "batchId": batch_file.batch_id,
                "issues_count": batch_file.issues_count or 0,
                "issuesCount": batch_file.issues_count or 0,
                "errors_count": batch_file.errors_count or 0,
                "errorsCount": batch_file.errors_count or 0,
                "warnings_count": batch_file.warnings_count or 0,
                "warningsCount": batch_file.warnings_count or 0,
                "suggestions_count": batch_file.suggestions_count or 0,
                "suggestionsCount": batch_file.suggestions_count or 0,
                "lines_of_code": lines_count,
                "linesOfCode": lines_count,
                "created_at": batch_file.created_at.isoformat(),
                "createdAt": batch_file.created_at.isoformat(),
                "completed_at": batch_file.completed_at.isoformat() if batch_file.completed_at else None,
                "completedAt": batch_file.completed_at.isoformat() if batch_file.completed_at else None
            })
        
        # Sort by created_at descending
        all_analyses.sort(key=lambda x: x["createdAt"], reverse=True)
        
        # Apply pagination
        total_count = len(all_analyses)
        offset = (page - 1) * page_size
        paginated_analyses = all_analyses[offset:offset + page_size]
        
        print(f"DEBUG: Total count: {total_count}, returning {len(paginated_analyses)} analyses")
        
        # Calculate pagination info
        has_next = offset + page_size < total_count
        has_previous = page > 1
        
        return {
            "analyses": paginated_analyses,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_next": has_next,
            "has_previous": has_previous
        }
    except Exception as e:
        print(f"ERROR in get_analysis_history: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "analyses": [],
            "total_count": 0,
            "page": page,
            "page_size": page_size,
            "has_next": False,
            "has_previous": False
        }

@router.get("/batch/{batch_file_id}", status_code=200)
async def get_batch_file_analysis(
    batch_file_id: str = Path(..., description="Batch file ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis results for a specific batch file.
    
    Requirements covered: 2.1, 5.1
    """
    try:
        from app.models.file_batch import BatchFile, FileStatus
        
        # Get the batch file
        batch_file = db.query(BatchFile).join(
            FileBatch, BatchFile.batch_id == FileBatch.id
        ).filter(
            BatchFile.id == batch_file_id,
            FileBatch.user_id == current_user.id
        ).first()
        
        if not batch_file:
            raise HTTPException(status_code=404, detail="Batch file analysis not found")
        
        # Structure the response similar to direct analysis
        lines_count = len(batch_file.file_content.split('\n')) if batch_file.file_content else 0
        file_size_kb = round(batch_file.file_size_bytes / 1024, 2) if batch_file.file_size_bytes else 0
        completed_status = "completed" if batch_file.status == FileStatus.COMPLETED else "failed"

        return {
            "analysis_id": str(batch_file.id),
            "id": str(batch_file.id),
            "type": "batch",
            "status": completed_status,
            "language": batch_file.language,
            "filename": batch_file.filename,
            "batch_id": batch_file.batch_id,
            "batchId": batch_file.batch_id,
            "file_size_kb": file_size_kb,
            "fileSizeKb": file_size_kb,
            "lines_count": lines_count,
            "linesCount": lines_count,
            "created_at": batch_file.created_at.isoformat(),
            "createdAt": batch_file.created_at.isoformat(),
            "completed_at": batch_file.completed_at.isoformat() if batch_file.completed_at else None,
            "completedAt": batch_file.completed_at.isoformat() if batch_file.completed_at else None,
            "processing_time_seconds": batch_file.processing_time_seconds,
            "processingTimeSeconds": batch_file.processing_time_seconds,
            "issues": batch_file.analysis_results or [],
            "metrics": batch_file.analysis_metrics or {},
            "summary": batch_file.analysis_summary or "",
            "issues_count": batch_file.issues_count or 0,
            "issuesCount": batch_file.issues_count or 0,
            "errors_count": batch_file.errors_count or 0,
            "errorsCount": batch_file.errors_count or 0,
            "warnings_count": batch_file.warnings_count or 0,
            "warningsCount": batch_file.warnings_count or 0,
            "suggestions_count": batch_file.suggestions_count or 0,
            "suggestionsCount": batch_file.suggestions_count or 0,
            "error_message": batch_file.error_message,
            "errorMessage": batch_file.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in get_batch_file_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve batch file analysis")

@router.get("/direct/stats", status_code=200)
async def get_analysis_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's analysis statistics and insights.
    
    Requirements covered: 5.1, 5.2
    """
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Basic counts
        total_analyses = db.query(DirectAnalysis).filter(DirectAnalysis.user_id == current_user.id).count()
        completed_analyses = db.query(DirectAnalysis).filter(
            DirectAnalysis.user_id == current_user.id,
            DirectAnalysis.status == "completed"
        ).count()
        failed_analyses = db.query(DirectAnalysis).filter(
            DirectAnalysis.user_id == current_user.id,
            DirectAnalysis.status == "failed"
        ).count()
        
        # Aggregate statistics
        stats_query = db.query(
            func.sum(DirectAnalysis.issues_count).label('total_issues'),
            func.sum(DirectAnalysis.lines_of_code).label('total_lines'),
            func.avg(DirectAnalysis.issues_count).label('avg_issues')
        ).filter(
            DirectAnalysis.user_id == current_user.id,
            DirectAnalysis.status == "completed"
        ).first()
        
        total_issues_found = int(stats_query.total_issues or 0)
        total_lines_analyzed = int(stats_query.total_lines or 0)
        avg_issues_per_analysis = float(stats_query.avg_issues or 0)
        
        # Languages used
        languages_query = db.query(DirectAnalysis.language).filter(
            DirectAnalysis.user_id == current_user.id
        ).distinct().all()
        languages_used = [lang[0] for lang in languages_query]
        
        # Time-based statistics
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        analyses_this_week = db.query(DirectAnalysis).filter(
            DirectAnalysis.user_id == current_user.id,
            DirectAnalysis.created_at >= week_ago
        ).count()
        
        analyses_this_month = db.query(DirectAnalysis).filter(
            DirectAnalysis.user_id == current_user.id,
            DirectAnalysis.created_at >= month_ago
        ).count()
        
        # Most common issue types (simplified - could be enhanced with actual issue categorization)
        most_common_issue_types = [
            {"category": "ai-review", "count": total_issues_found, "percentage": 100.0}
        ] if total_issues_found > 0 else []
        
        return {
            "total_analyses": total_analyses,
            "completed_analyses": completed_analyses,
            "failed_analyses": failed_analyses,
            "total_issues_found": total_issues_found,
            "total_lines_analyzed": total_lines_analyzed,
            "languages_used": languages_used,
            "avg_issues_per_analysis": round(avg_issues_per_analysis, 2),
            "most_common_issue_types": most_common_issue_types,
            "analyses_this_week": analyses_this_week,
            "analyses_this_month": analyses_this_month
        }
    except Exception as e:
        print(f"Error getting analysis stats: {str(e)}")
        # Return empty stats if there's an error (likely table doesn't exist yet)
        return {
            "total_analyses": 0,
            "completed_analyses": 0,
            "failed_analyses": 0,
            "total_issues_found": 0,
            "total_lines_analyzed": 0,
            "languages_used": [],
            "avg_issues_per_analysis": 0.0,
            "most_common_issue_types": [],
            "analyses_this_week": 0,
            "analyses_this_month": 0
        }

@router.delete("/direct/{analysis_id}")
async def delete_direct_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific direct analysis.
    
    Users can only delete their own analyses.
    """
    analysis = db.query(DirectAnalysis).filter(
        DirectAnalysis.id == analysis_id,
        DirectAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    db.delete(analysis)
    db.commit()
    
    return {"message": "Analysis deleted successfully", "analysis_id": analysis_id}

# This route must come LAST to avoid conflicts with specific routes like /direct/history
@router.get("/direct/{analysis_id}")
async def get_direct_analysis_by_id(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific analysis by ID (handles both direct and repository analyses).
    
    Users can only access their own analyses.
    """
    try:
        # Try direct analysis first
        analysis = db.query(DirectAnalysis).filter(
            DirectAnalysis.id == analysis_id,
            DirectAnalysis.user_id == current_user.id
        ).first()
        
        if analysis:
            # Convert stored results back to response format
            if analysis.results and analysis.status == "completed":
                stored_results = analysis.results
                
                return {
                    "analysis_id": analysis.id,
                    "type": "direct",
                    "status": analysis.status,
                    "issues": stored_results.get("issues", []),
                    "metrics": stored_results.get("metrics", {}),
                    "summary": stored_results.get("summary", ""),
                    "created_at": analysis.created_at.isoformat(),
                    "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                    "language": analysis.language,
                    "filename": analysis.filename,
                    "file_size_bytes": analysis.file_size_bytes or 0,
                    "processing_time_ms": stored_results.get("processing_time_ms"),
                    "ai_model_used": stored_results.get("ai_model_used")
                }
            else:
                # Return minimal response for failed or pending analyses
                return {
                    "analysis_id": analysis.id,
                    "type": "direct",
                    "status": analysis.status,
                    "issues": [],
                    "metrics": {
                        "lines_of_code": analysis.lines_of_code or 0,
                        "total_lines": analysis.lines_of_code or 0,
                        "complexity": 0,
                        "maintainability_index": 0,
                        "duplicate_lines": 0,
                        "test_coverage": None,
                        "comment_lines": 0,
                        "blank_lines": 0,
                        "function_count": 0,
                        "class_count": 0,
                        "comment_ratio": 0.0,
                        "complexity_per_function": None
                    },
                    "summary": analysis.error_message or "Analysis failed",
                    "created_at": analysis.created_at.isoformat(),
                    "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                    "language": analysis.language,
                    "filename": analysis.filename,
                    "file_size_bytes": analysis.file_size_bytes or 0
                }
        
        # Try repository analysis
        from app.models.github_integration import PRAnalysis, GitHubRepository
        repo_analysis = db.query(PRAnalysis).join(
            GitHubRepository, PRAnalysis.repository_id == GitHubRepository.id
        ).filter(
            PRAnalysis.id == analysis_id,
            GitHubRepository.user_id == current_user.id
        ).first()
        
        if repo_analysis:
            repo = db.query(GitHubRepository).filter(GitHubRepository.id == repo_analysis.repository_id).first()
            
            # Extract issues from analysis_results
            issues = []
            if repo_analysis.analysis_results and isinstance(repo_analysis.analysis_results, dict):
                raw_issues = repo_analysis.analysis_results.get('issues', [])
                for idx, issue in enumerate(raw_issues):
                    file_path = issue.get('file_path')
                    # Handle None, null, empty string, or "None" string
                    if not file_path or file_path == 'None' or file_path == 'null':
                        file_path = 'Unknown file'
                    
                    line_num = issue.get('line_number', 0)
                    message = issue.get('comment', issue.get('message', 'No description'))
                    
                    # Prepend file path to message for clarity
                    full_message = f"[{file_path}:{line_num}] {message}"
                    
                    issues.append({
                        "id": issue.get('id', f"{repo_analysis.id}-{idx}"),
                        "line": line_num,
                        "column": 1,
                        "severity": issue.get('severity', 'info'),
                        "message": full_message,
                        "rule": "gemini-ai-review",
                        "category": "ai-review",
                        "suggestion": issue.get('comment', ''),
                        "file_path": file_path
                    })
            
            return {
                "analysis_id": repo_analysis.id,
                "type": "repository",
                "status": repo_analysis.status.value if hasattr(repo_analysis.status, 'value') else str(repo_analysis.status),
                "issues": issues,
                "metrics": {
                    "files_analyzed": repo_analysis.analysis_results.get('summary', {}).get('files_analyzed', 0) if repo_analysis.analysis_results else 0,
                    "issues_found": repo_analysis.issues_found or 0,
                    "errors_count": repo_analysis.errors_count or 0,
                    "warnings_count": repo_analysis.warnings_count or 0
                },
                "summary": f"Repository analysis completed. {repo_analysis.issues_found or 0} issues found across multiple files.",
                "created_at": repo_analysis.created_at.isoformat(),
                "completed_at": repo_analysis.completed_at.isoformat() if repo_analysis.completed_at else None,
                "language": "multiple",
                "filename": f"Full Repository Analysis - {repo.repo_name if repo else 'Unknown'}",
                "repository_name": repo.repo_name if repo else "Unknown",
                "repository_id": repo_analysis.repository_id
            }
        
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting analysis by ID: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")


# Response models for issue endpoints
class IssueDetailResponse(BaseModel):
    """Detailed response for a single issue."""
    issue_id: str
    analysis_id: str
    pattern_type: str
    severity: str
    category: Optional[str]
    location: dict
    suggestion_text: str
    code_context: str
    original_code: Optional[str]
    suggested_fix: Optional[str]
    ast_node_type: Optional[str]
    ast_metadata: Optional[dict]
    status: str
    confidence_score: Optional[float]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]
    feedback_summary: dict
    feedback_interface: dict

class IssueListItem(BaseModel):
    """Summary response for issue in a list."""
    issue_id: str
    pattern_type: str
    severity: str
    category: Optional[str]
    location: dict
    suggestion_text: str
    code_context: str
    status: str
    confidence_score: Optional[float]
    created_at: str
    feedback_count: int
    has_accepted_feedback: bool
    has_rejected_feedback: bool

class AnalysisIssuesResponse(BaseModel):
    """Response for analysis issues endpoint."""
    analysis_id: str
    issues: List[IssueListItem]
    pagination: dict
    filters: dict
    summary: dict
    feedback_interface: dict

# New endpoints for issue retrieval (Task 9.2)

@router.get("/issues/{issue_id}", response_model=IssueDetailResponse)
async def get_issue_by_id(
    issue_id: str = Path(..., description="Unique issue identifier"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific issue by its ID.
    
    Users can only access issues from their own analyses.
    
    Requirements covered: 1.4, 5.1
    """
    try:
        # Import Issue model
        from app.models.feedback import Issue
        
        # Query issue with user permission check via analysis relationship
        issue = db.query(Issue).join(DirectAnalysis).filter(
            Issue.id == issue_id,
            DirectAnalysis.user_id == current_user.id
        ).first()
        
        if not issue:
            raise HTTPException(
                status_code=404, 
                detail="Issue not found or you don't have permission to access it"
            )
        
        # Format response with comprehensive issue details
        response = {
            "issue_id": issue.id,
            "analysis_id": issue.analysis_id,
            "pattern_type": issue.pattern_type,
            "severity": issue.severity,
            "category": issue.category,
            "location": issue.location,
            "suggestion_text": issue.suggestion_text,
            "code_context": issue.code_context,
            "original_code": issue.original_code,
            "suggested_fix": issue.suggested_fix,
            "ast_node_type": issue.ast_node_type,
            "ast_metadata": issue.ast_metadata,
            "status": issue.status,
            "confidence_score": issue.confidence_score,
            "created_at": issue.created_at.isoformat(),
            "updated_at": issue.updated_at.isoformat(),
            "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
            # Feedback summary
            "feedback_summary": {
                "total_feedback": len(issue.feedback_records),
                "accepted": len([f for f in issue.feedback_records if f.feedback_type == "accept"]),
                "rejected": len([f for f in issue.feedback_records if f.feedback_type == "reject"]),
                "modified": len([f for f in issue.feedback_records if f.feedback_type == "modify"])
            },
            # Feedback interface
            "feedback_interface": {
                "can_provide_feedback": issue.status == "active",
                "feedback_endpoint": f"/api/v1/feedback",
                "supported_actions": ["accept", "reject", "modify"] if issue.status == "active" else []
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving issue {issue_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve issue details"
        )


@router.get("/analyses/{analysis_id}/issues", response_model=AnalysisIssuesResponse)
async def get_analysis_issues(
    analysis_id: str = Path(..., description="Analysis identifier"),
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, error)"),
    status: Optional[str] = Query(None, description="Filter by status (active, resolved, ignored)"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all issues for a specific analysis with filtering and pagination.
    
    Users can only access issues from their own analyses.
    
    Requirements covered: 1.4, 5.1
    """
    try:
        # Import Issue model
        from app.models.feedback import Issue
        
        # Verify analysis exists and belongs to user
        analysis = db.query(DirectAnalysis).filter(
            DirectAnalysis.id == analysis_id,
            DirectAnalysis.user_id == current_user.id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found or you don't have permission to access it"
            )
        
        # Build query with filters
        query = db.query(Issue).filter(Issue.analysis_id == analysis_id)
        
        if severity:
            query = query.filter(Issue.severity == severity.lower())
        if status:
            query = query.filter(Issue.status == status.lower())
        if pattern_type:
            query = query.filter(Issue.pattern_type == pattern_type)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        issues = query.order_by(Issue.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Format issues for response
        formatted_issues = []
        for issue in issues:
            formatted_issue = {
                "issue_id": issue.id,
                "pattern_type": issue.pattern_type,
                "severity": issue.severity,
                "category": issue.category,
                "location": issue.location,
                "suggestion_text": issue.suggestion_text,
                "code_context": issue.code_context[:200] + "..." if len(issue.code_context) > 200 else issue.code_context,
                "status": issue.status,
                "confidence_score": issue.confidence_score,
                "created_at": issue.created_at.isoformat(),
                "feedback_count": len(issue.feedback_records),
                "has_accepted_feedback": any(f.feedback_type == "accept" for f in issue.feedback_records),
                "has_rejected_feedback": any(f.feedback_type == "reject" for f in issue.feedback_records)
            }
            formatted_issues.append(formatted_issue)
        
        # Calculate pagination info
        has_next = offset + page_size < total_count
        has_previous = page > 1
        total_pages = (total_count + page_size - 1) // page_size
        
        # Get summary statistics
        severity_counts = {}
        status_counts = {}
        pattern_counts = {}
        
        all_issues = db.query(Issue).filter(Issue.analysis_id == analysis_id).all()
        for issue in all_issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            status_counts[issue.status] = status_counts.get(issue.status, 0) + 1
            pattern_counts[issue.pattern_type] = pattern_counts.get(issue.pattern_type, 0) + 1
        
        response = {
            "analysis_id": analysis_id,
            "issues": formatted_issues,
            "pagination": {
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous
            },
            "filters": {
                "severity": severity,
                "status": status,
                "pattern_type": pattern_type
            },
            "summary": {
                "total_issues": total_count,
                "severity_distribution": severity_counts,
                "status_distribution": status_counts,
                "pattern_distribution": pattern_counts
            },
            "feedback_interface": {
                "feedback_endpoint": f"/api/v1/feedback",
                "bulk_feedback_endpoint": f"/api/v1/feedback/bulk",
                "supported_actions": ["accept", "reject", "modify"]
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving issues for analysis {analysis_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve analysis issues"
        )


# ============================================================================
# WebSocket Endpoint for Real-Time Analysis Status Updates
# Requirements covered: 13.1, 13.2, 13.3
# ============================================================================

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json

@router.websocket("/ws/analysis/{analysis_id}")
async def analysis_status_websocket(
    websocket: WebSocket,
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time analysis status updates.
    
    Clients can connect to this endpoint to receive real-time updates
    about the status of their analysis job.
    
    Requirements covered: 13.1, 13.2, 13.3
    """
    await websocket.accept()
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "analysis_id": analysis_id,
            "message": "Connected to analysis status stream"
        })
        
        # Poll for status updates
        last_status = None
        max_iterations = 300  # 5 minutes with 1-second intervals
        iteration = 0
        
        while iteration < max_iterations:
            try:
                # Query analysis status
                analysis = db.query(DirectAnalysis).filter(
                    DirectAnalysis.id == analysis_id
                ).first()
                
                if not analysis:
                    await websocket.send_json({
                        "type": "error",
                        "analysis_id": analysis_id,
                        "message": "Analysis not found"
                    })
                    break
                
                # Check if status changed
                current_status = analysis.status
                if current_status != last_status:
                    # Send status update
                    update_data = {
                        "type": "status_update",
                        "analysis_id": analysis_id,
                        "status": analysis.status,
                        "updated_at": analysis.completed_at.isoformat() if analysis.completed_at else datetime.utcnow().isoformat()
                    }
                    
                    # Add results if completed
                    if analysis.status == "completed":
                        update_data["results_available"] = True
                        update_data["issues_count"] = analysis.issues_count
                        update_data["errors_count"] = analysis.errors_count
                        update_data["warnings_count"] = analysis.warnings_count
                    
                    # Add error info if failed
                    if analysis.status == "failed":
                        update_data["error_message"] = analysis.error_message
                    
                    await websocket.send_json(update_data)
                    last_status = current_status
                
                # Break if analysis is complete or failed
                if analysis.status in ["completed", "failed"]:
                    await websocket.send_json({
                        "type": "final",
                        "analysis_id": analysis_id,
                        "status": analysis.status,
                        "message": "Analysis processing complete"
                    })
                    break
                
                # Wait before next poll
                await asyncio.sleep(1)
                iteration += 1
                
            except Exception as e:
                logger.error(f"Error in WebSocket status update: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "analysis_id": analysis_id,
                    "message": f"Error getting status: {str(e)}"
                })
                break
        
        # Timeout reached
        if iteration >= max_iterations:
            await websocket.send_json({
                "type": "timeout",
                "analysis_id": analysis_id,
                "message": "Status monitoring timeout reached"
            })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for analysis {analysis_id}")
    except Exception as e:
        logger.error(f"WebSocket error for analysis {analysis_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "analysis_id": analysis_id,
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/batch/{batch_id}")
async def batch_status_websocket(
    websocket: WebSocket,
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time batch processing status updates.
    
    Clients can connect to this endpoint to receive real-time updates
    about the status of their batch processing job.
    
    Requirements covered: 13.1, 13.2, 13.3
    """
    await websocket.accept()
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "batch_id": batch_id,
            "message": "Connected to batch status stream"
        })
        
        # Poll for status updates
        last_status = None
        last_processed = 0
        max_iterations = 600  # 10 minutes with 1-second intervals
        iteration = 0
        
        while iteration < max_iterations:
            try:
                # Query batch status
                batch = db.query(FileBatch).filter(
                    FileBatch.id == batch_id
                ).first()
                
                if not batch:
                    await websocket.send_json({
                        "type": "error",
                        "batch_id": batch_id,
                        "message": "Batch not found"
                    })
                    break
                
                # Check if status or progress changed
                current_status = batch.status
                current_processed = batch.processed_files
                
                if current_status != last_status or current_processed != last_processed:
                    # Send status update
                    update_data = {
                        "type": "status_update",
                        "batch_id": batch_id,
                        "status": batch.status,
                        "total_files": batch.total_files,
                        "processed_files": batch.processed_files,
                        "successful_files": batch.successful_files,
                        "failed_files": batch.failed_files,
                        "progress_percentage": batch.progress_percentage,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    await websocket.send_json(update_data)
                    last_status = current_status
                    last_processed = current_processed
                
                # Break if batch is complete
                if batch.is_complete:
                    await websocket.send_json({
                        "type": "final",
                        "batch_id": batch_id,
                        "status": batch.status,
                        "message": "Batch processing complete",
                        "successful_files": batch.successful_files,
                        "failed_files": batch.failed_files
                    })
                    break
                
                # Wait before next poll
                await asyncio.sleep(1)
                iteration += 1
                
            except Exception as e:
                logger.error(f"Error in WebSocket batch status update: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "batch_id": batch_id,
                    "message": f"Error getting status: {str(e)}"
                })
                break
        
        # Timeout reached
        if iteration >= max_iterations:
            await websocket.send_json({
                "type": "timeout",
                "batch_id": batch_id,
                "message": "Status monitoring timeout reached"
            })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for batch {batch_id}")
    except Exception as e:
        logger.error(f"WebSocket error for batch {batch_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "batch_id": batch_id,
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# ============================================================================
# Polling Fallback Endpoints for Status Updates
# Requirements covered: 13.1, 13.2, 13.3
# ============================================================================

@router.get("/direct/{analysis_id}/status")
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the current status of an analysis (polling fallback).
    
    This endpoint provides a polling-based alternative to WebSocket
    for clients that cannot use WebSocket connections.
    
    Requirements covered: 13.1, 13.3
    """
    try:
        analysis = db.query(DirectAnalysis).filter(
            DirectAnalysis.id == analysis_id,
            DirectAnalysis.user_id == current_user.id
        ).first()
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found or access denied"
            )
        
        response = {
            "analysis_id": analysis.id,
            "status": analysis.status,
            "created_at": analysis.created_at.isoformat(),
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "filename": analysis.filename,
            "language": analysis.language
        }
        
        # Add results summary if completed
        if analysis.status == "completed":
            response["issues_count"] = analysis.issues_count
            response["errors_count"] = analysis.errors_count
            response["warnings_count"] = analysis.warnings_count
            response["results_available"] = True
        
        # Add error info if failed
        if analysis.status == "failed":
            response["error_message"] = analysis.error_message
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analysis status: {str(e)}"
        )

@router.get("/repository/{repository_analysis_id}", status_code=200)
async def get_repository_analysis(
    repository_analysis_id: str = Path(..., description="Repository analysis ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed analysis results for a specific repository analysis.
    """
    try:
        from app.models.github_integration import PRAnalysis, GitHubRepository
        from uuid import UUID
        logger.info(f"Fetching repository analysis for ID: {repository_analysis_id}")
        
        try:
            # Try to convert to UUID first
            analysis_id = UUID(repository_analysis_id)
            logger.debug(f"Converted {repository_analysis_id} to UUID: {analysis_id}")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not convert {repository_analysis_id} to UUID, using as string: {str(e)}")
            analysis_id = repository_analysis_id
        
        logger.debug(f"Querying database for analysis with ID: {analysis_id}")
        
        # Convert analysis_id to string for the query since the database stores it as VARCHAR
        analysis_id_str = str(analysis_id)
        
        # Use text() to ensure proper type casting in the query
        from sqlalchemy import text
        
        # First try with the ID as a string (VARCHAR)
        analysis = db.query(PRAnalysis).join(
            GitHubRepository, PRAnalysis.repository_id == GitHubRepository.id
        ).filter(
            PRAnalysis.id == analysis_id_str,
            GitHubRepository.user_id == current_user.id
        ).first()
        
        # If not found, try with the ID as a UUID (if it was provided as UUID string)
        if not analysis and isinstance(analysis_id, UUID):
            analysis = db.query(PRAnalysis).join(
                GitHubRepository, PRAnalysis.repository_id == GitHubRepository.id
            ).filter(
                text("pr_analyses.id::uuid = :id").params(id=str(analysis_id)),
                GitHubRepository.user_id == current_user.id
            ).first()

        if not analysis:
            logger.warning(f"Analysis not found for ID: {analysis_id}")
            raise HTTPException(status_code=404, detail="Repository analysis not found")

        logger.debug(f"Found analysis: {analysis.id}, fetching repository details")
        repo = db.query(GitHubRepository).filter(GitHubRepository.id == analysis.repository_id).first()
        
        if not repo:
            logger.error(f"Repository not found for analysis ID: {analysis_id}")
            raise HTTPException(status_code=404, detail="Repository not found")

        # Normalize stored results into a stable structure for the frontend
        raw_results = analysis.analysis_results or {}

        raw_issues = raw_results.get("issues") or []
        normalized_issues = []
        for idx, issue in enumerate(raw_issues):
            issue_id = (
                issue.get("id")
                or issue.get("issue_id")
                or issue.get("reference_id")
                or issue.get("uuid")
                or f"{analysis.id}-issue-{idx}"
            )

            normalized_issues.append(
                {
                    "id": issue_id,
                    "line": issue.get("line")
                    or issue.get("line_number")
                    or issue.get("start_line")
                    or 0,
                    "column": issue.get("column")
                    or issue.get("column_number")
                    or issue.get("start_column")
                    or 0,
                    "severity": (issue.get("severity") or "info").lower(),
                    "message": issue.get("message")
                    or issue.get("comment")
                    or issue.get("description")
                    or "",
                    "rule": issue.get("rule") or issue.get("rule_id") or "ai-analysis",
                    "category": issue.get("category")
                    or issue.get("type")
                    or "ai-review",
                    "suggestion": issue.get("suggestion")
                    or issue.get("recommendation")
                    or issue.get("fix"),
                    "file_path": issue.get("file_path")
                    or issue.get("file")
                    or issue.get("path"),
                }
            )

        # Merge metrics from stored results and summary data when available
        metrics_payload = raw_results.get("metrics") or {}
        summary_payload = raw_results.get("summary") or {}
        if summary_payload:
            metrics_payload = {**metrics_payload}
            for key, value in summary_payload.items():
                metrics_payload.setdefault(key, value)

        # Prepare response data
        response_data = {
            "analysis_id": str(analysis.id),
            "type": "repository",
            "status": analysis.status.value if hasattr(analysis.status, 'value') else str(analysis.status),
            "language": "multiple",
            "filename": f"Full Repository Analysis - {repo.repo_name if repo else 'Unknown'}",
            "repository_name": repo.repo_name if repo else "Unknown",
            "repository_id": str(analysis.repository_id),
            "issues": normalized_issues,
            "metrics": metrics_payload,
            "summary": raw_results.get("summary_message")
            or raw_results.get("summary")
            or raw_results.get("message")
            or "",
            "suggestions": raw_results.get("suggestions") or [],
            "created_at": analysis.created_at.isoformat(),
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "processing_time": raw_results.get("processing_time")
            or raw_results.get("processing_time_ms")
            or None,
            "issues_count": analysis.issues_found or len(normalized_issues),
            "errors_count": analysis.errors_count or 0,
            "warnings_count": analysis.warnings_count or 0,
            "analysis_results": raw_results,
        }

        return response_data

    except HTTPException as he:
        logger.error(f"HTTPException in get_repository_analysis: {str(he)}")
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Unexpected error in get_repository_analysis: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching the repository analysis: {str(e)}"
        )
