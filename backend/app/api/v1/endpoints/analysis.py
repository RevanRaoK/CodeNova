# app/api/v1/endpoints/analysis.py

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Path, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.database import get_db, SessionLocal
from app.services.repository_services import repository_service
from app.db import models
from app.models.analysis import DirectAnalysis
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.users import User
from app.schemas.analysis import (
    DirectAnalysisResponse, CodeIssue, CodeMetrics, AnalysisStatus,
    DirectAnalysisHistoryItem, AnalysisHistoryResponse, AnalysisStatsResponse
)
from pydantic import BaseModel, Field, validator

router = APIRouter()

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
    filename: Optional[str] = Field(
        default=None, 
        max_length=255,
        description="Optional filename for context"
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
def analyze_code_direct(
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
    from app.services.ai_service import aiservice  # local import
    from app.utils.ast_parser import ASTParser
    from app.services.issue_id_service import IssueIDService
    
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    
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
        
        # Get code review suggestions from Gemini AI
        print("Calling AI service...")
        suggestions = aiservice.get_review_for_code(request.code)
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
                "suggestion": suggestion.get('suggestion', suggestion.get('comment', ''))
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
            db.commit()
            print("Analysis results stored successfully!")
            
        except Exception as db_error:
            # Log database error but don't fail the analysis
            print(f"Warning: Failed to store analysis results in database: {str(db_error)}")
            import traceback
            traceback.print_exc()
            db.rollback()
        
        return {
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
            "ai_model_used": "gemini-ai"
        }
        
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
def get_analysis_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    language: Optional[str] = Query(default=None, description="Filter by programming language"),
    status: Optional[str] = Query(default=None, description="Filter by analysis status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's analysis history with pagination and filtering.
    
    Requirements covered: 2.1, 5.1, 5.2
    """
    print(f"DEBUG: get_analysis_history called for user {current_user.id}")
    try:
        # Build query
        print(f"DEBUG: Building query for user_id {current_user.id}")
        query = db.query(DirectAnalysis).filter(DirectAnalysis.user_id == current_user.id)
        
        # Apply filters
        if language:
            print(f"DEBUG: Filtering by language: {language}")
            query = query.filter(DirectAnalysis.language == language.lower())
        if status:
            print(f"DEBUG: Filtering by status: {status}")
            query = query.filter(DirectAnalysis.status == status.lower())
        
        # Get total count
        total_count = query.count()
        print(f"DEBUG: Total count: {total_count}")
        
        # Apply pagination
        offset = (page - 1) * page_size
        analyses = query.order_by(DirectAnalysis.created_at.desc()).offset(offset).limit(page_size).all()
        print(f"DEBUG: Found {len(analyses)} analyses after pagination")
        
        # Convert to response format
        history_items = []
        for analysis in analyses:
            history_items.append({
                "analysis_id": analysis.id,
                "status": analysis.status,
                "language": analysis.language,
                "filename": analysis.filename,
                "issues_count": analysis.issues_count or 0,
                "errors_count": analysis.errors_count or 0,
                "warnings_count": analysis.warnings_count or 0,
                "lines_of_code": analysis.lines_of_code,
                "created_at": analysis.created_at.isoformat(),
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
            })
        
        # Calculate pagination info
        has_next = offset + page_size < total_count
        has_previous = page > 1
        
        return {
            "analyses": history_items,
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

@router.get("/direct/stats", status_code=200)
def get_analysis_stats(
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
def delete_direct_analysis(
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
def get_direct_analysis_by_id(
    analysis_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific direct analysis by ID.
    
    Users can only access their own analyses.
    """
    try:
        analysis = db.query(DirectAnalysis).filter(
            DirectAnalysis.id == analysis_id,
            DirectAnalysis.user_id == current_user.id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Convert stored results back to response format
        if analysis.results and analysis.status == "completed":
            stored_results = analysis.results
            
            return {
                "analysis_id": analysis.id,
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting analysis by ID: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")
