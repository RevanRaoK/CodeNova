"""
AI Analysis Endpoints

This module provides API endpoints for AI-powered code analysis with personalization.
It includes endpoints for personalized code review that learns from user feedback.

Requirements covered: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.3, 8.4, 8.5, 8.6
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_active_user
from app.models.users import User
from app.models.analysis import DirectAnalysis
from app.models.feedback import Issue
from pydantic import BaseModel, Field, validator

router = APIRouter()


class PersonalizedAnalysisRequest(BaseModel):
    """Request model for personalized code analysis."""
    
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
            raise ValueError(
                f'Unsupported language: {v}. '
                f'Supported languages: {", ".join(supported_languages)}'
            )
        return v.lower()


class PersonalizedAnalysisResponse(BaseModel):
    """Response model for personalized code analysis."""
    
    analysis_id: str
    status: str
    issues: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    summary: str
    created_at: str
    completed_at: Optional[str]
    language: str
    filename: Optional[str]
    personalization_info: Dict[str, Any]
    processing_time_ms: int


@router.post("/analyze-with-learning", response_model=PersonalizedAnalysisResponse)
async def analyze_code_with_learning(
    request: PersonalizedAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze code with personalized AI learning from user feedback history.
    
    This endpoint uses the user's historical feedback patterns to generate
    code review suggestions that are more aligned with their preferences
    and coding standards. Recent feedback (last 30 days) is weighted more
    heavily to reflect current preferences.
    
    The AI will:
    - Prioritize issue categories the user typically accepts
    - Minimize or carefully justify categories the user typically rejects
    - Match the style and detail level of previously accepted suggestions
    - Provide unique, contextual suggestions tailored to the code
    
    Requirements covered: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.3, 8.4, 8.5, 8.6
    
    Args:
        request: PersonalizedAnalysisRequest with code and language
        current_user: Authenticated user from JWT token
        db: Database session
    
    Returns:
        PersonalizedAnalysisResponse with issues, metrics, and personalization info
    
    Raises:
        HTTPException: 413 if code is too large, 422 for validation errors, 500 for analysis errors
    """
    from app.services.ai_service import get_ai_service_for_user
    from app.services.personalized_prompt_builder import PersonalizedPromptBuilder
    
    analysis_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    
    print(f"Starting personalized analysis for user {current_user.id}, analysis_id: {analysis_id}")
    
    try:
        # Validate request size
        code_size_kb = len(request.code.encode('utf-8')) / 1024
        if code_size_kb > 100:
            raise HTTPException(
                status_code=413,
                detail=f"Code content too large: {code_size_kb:.1f}KB. Maximum allowed: 100KB"
            )
        
        # Get personalization summary
        prompt_builder = PersonalizedPromptBuilder(db)
        personalization_summary = prompt_builder.get_personalization_summary(current_user.id)
        
        print(f"Personalization available: {personalization_summary['has_personalization']}")
        
        # Get AI service configured with user's API key if available
        ai_service = get_ai_service_for_user(current_user.id, db)
        
        # Get personalized code review with learning pipeline integration
        suggestions = ai_service.get_personalized_review_for_code(
            code=request.code,
            language=request.language,
            user_id=current_user.id,
            analysis_id=analysis_id,
            db_session=db
        )
        
        print(f"AI service returned {len(suggestions)} personalized suggestions")
        
        # Transform suggestions to structured issue dictionaries
        issues = []
        issue_ids = []
        
        for suggestion in suggestions:
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
            
            issue_id = suggestion.get('issue_id', str(uuid.uuid4()))
            issue_ids.append(issue_id)
            
            issue = {
                "id": issue_id,
                "line": max(1, suggestion.get('line_number', 1)),
                "column": 1,
                "severity": severity,
                "message": suggestion.get('comment', 'No comment provided'),
                "rule": "gemini-ai-personalized",
                "category": "ai-review-personalized",
                "suggestion": suggestion.get('suggestion', suggestion.get('comment', '')),
                "personalized": suggestion.get('personalized', True),
                "ast_context": suggestion.get('ast_context')
            }
            issues.append(issue)
        
        # Calculate metrics
        lines = request.code.split('\n')
        lines_of_code = len([line for line in lines if line.strip()])
        total_lines = len(lines)
        
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'catch', 'switch', 'case']
        complexity = sum(request.code.lower().count(keyword) for keyword in complexity_keywords)
        
        avg_line_length = sum(len(line) for line in lines) / max(1, total_lines)
        maintainability_index = max(0, min(100, 100 - (complexity * 2) - (avg_line_length / 10)))
        
        metrics = {
            "lines_of_code": lines_of_code,
            "total_lines": total_lines,
            "complexity": complexity,
            "maintainability_index": int(maintainability_index),
            "duplicate_lines": 0,
            "test_coverage": None,
            "comment_lines": 0,
            "blank_lines": total_lines - lines_of_code,
            "function_count": 0,
            "class_count": 0,
            "comment_ratio": 0.0,
            "complexity_per_function": None
        }
        
        # Generate summary
        issue_count = len(issues)
        severity_counts = {}
        for issue in issues:
            severity = issue.get('severity', 'info')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary_parts = [
            f"Analyzed {lines_of_code} lines of {request.language} code with personalized AI learning"
        ]
        
        if personalization_summary['has_personalization']:
            summary_parts.append(
                f"(based on {personalization_summary['total_feedback']} feedback items, "
                f"{personalization_summary['recent_feedback']} recent)"
            )
        
        if issue_count > 0:
            summary_parts.append(f"Found {issue_count} issues")
            if severity_counts:
                severity_details = []
                for severity in ['error', 'warning', 'info', 'suggestion']:
                    if severity in severity_counts:
                        count = severity_counts[severity]
                        severity_details.append(f"{count} {severity}{'s' if count > 1 else ''}")
                if severity_details:
                    summary_parts.append(f"({', '.join(severity_details)})")
        else:
            summary_parts.append("No issues found")
        
        summary = ". ".join(summary_parts) + "."
        
        completed_at = datetime.utcnow()
        processing_time_ms = int((completed_at - created_at).total_seconds() * 1000)
        
        # Store analysis results in database
        print("Storing personalized analysis results in database...")
        try:
            errors_count = sum(1 for issue in issues if issue.get('severity') == 'error')
            warnings_count = sum(1 for issue in issues if issue.get('severity') == 'warning')
            
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
                    "ai_model_used": "gemini-ai-personalized",
                    "personalization_applied": personalization_summary['has_personalization']
                },
                lines_of_code=metrics["lines_of_code"],
                complexity_score=metrics["complexity"],
                maintainability_index=metrics["maintainability_index"],
                issues_count=len(issues),
                errors_count=errors_count,
                warnings_count=warnings_count,
                file_size_bytes=len(request.code.encode('utf-8')),
                issue_ids=issue_ids
            )
            
            db.add(db_analysis)
            
            # Create Issue records
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
                    category=issue_data.get("category", "ai-review-personalized"),
                    location={
                        "line": issue_data["line"],
                        "column": issue_data["column"],
                        "context": issue_data.get("suggestion", "")[:100]
                    },
                    suggestion_text=issue_data["message"],
                    code_context=request.code[max(0, (issue_data["line"]-3)*50):(issue_data["line"]+3)*50],
                    original_code="",
                    suggested_fix=issue_data.get("suggestion", ""),
                    ast_node_type=None,
                    ast_metadata=issue_data.get("ast_context"),
                    status="active",
                    confidence_score=0.85  # Higher confidence for personalized suggestions
                )
                db.add(db_issue)
            
            db.commit()
            print(f"Personalized analysis results and {len(issues)} issues stored successfully!")
            
        except Exception as db_error:
            print(f"Warning: Failed to store analysis results in database: {str(db_error)}")
            import traceback
            traceback.print_exc()
            db.rollback()
        
        # Build response
        response = PersonalizedAnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            issues=issues,
            metrics=metrics,
            summary=summary,
            created_at=created_at.isoformat(),
            completed_at=completed_at.isoformat(),
            language=request.language,
            filename=request.filename,
            personalization_info={
                "enabled": personalization_summary['has_personalization'],
                "total_feedback": personalization_summary['total_feedback'],
                "recent_feedback": personalization_summary['recent_feedback'],
                "accepted_count": personalization_summary.get('accepted_count', 0),
                "rejected_count": personalization_summary.get('rejected_count', 0),
                "top_accepted_categories": personalization_summary.get('top_accepted_categories', []),
                "top_rejected_categories": personalization_summary.get('top_rejected_categories', []),
                "message": personalization_summary['message']
            },
            processing_time_ms=processing_time_ms
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Store failed analysis
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
                warnings_count=0
            )
            db.add(failed_analysis)
            db.commit()
        except Exception as db_error:
            print(f"Failed to store failed analysis: {str(db_error)}")
            db.rollback()
        
        import traceback
        print(f"Error in personalized analysis for user {current_user.id}: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Personalized code analysis failed: {str(e)}"
        )


@router.get("/personalization-status")
async def get_personalization_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the personalization status for the current user.
    
    This endpoint provides information about what personalization data
    is available for the user without performing an analysis.
    
    Returns:
        Dictionary with personalization summary including:
        - has_personalization: Whether personalization is available
        - total_feedback: Total feedback count
        - recent_feedback: Recent feedback count (last 30 days)
        - top_accepted_categories: Categories user frequently accepts
        - top_rejected_categories: Categories user frequently rejects
    
    Requirements covered: 8.10
    """
    from app.services.personalized_prompt_builder import PersonalizedPromptBuilder
    
    try:
        prompt_builder = PersonalizedPromptBuilder(db)
        personalization_summary = prompt_builder.get_personalization_summary(current_user.id)
        
        return {
            "user_id": current_user.id,
            "personalization": personalization_summary
        }
        
    except Exception as e:
        print(f"Error getting personalization status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get personalization status: {str(e)}"
        )


@router.get("/learning-status")
async def get_learning_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the learning pipeline status for the current user.
    
    This endpoint provides comprehensive information about the user's
    learning patterns, including boosted and reduced patterns based on
    feedback consistency.
    
    Returns:
        Dictionary with learning status including:
        - learning_active: Whether learning is active for the user
        - total_patterns: Total number of learning patterns
        - boosted_patterns: Patterns with increased priority
        - reduced_patterns: Patterns with decreased priority
        - effectiveness: Learning effectiveness metrics
    
    Requirements covered: 8.10
    """
    from app.services.learning_pipeline_service import LearningPipelineService
    
    try:
        learning_service = LearningPipelineService(db)
        learning_status = learning_service.get_learning_status(current_user.id)
        
        return {
            "user_id": current_user.id,
            "learning_status": learning_status
        }
        
    except Exception as e:
        print(f"Error getting learning status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning status: {str(e)}"
        )


@router.post("/trigger-learning-update")
async def trigger_learning_update(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger a learning pipeline update for the current user.
    
    This endpoint allows users to manually update their learning patterns
    based on recent feedback. Normally this happens automatically when
    feedback is provided, but this endpoint allows for manual updates.
    
    Returns:
        Dictionary with update results including:
        - updated_patterns: Number of patterns updated
        - priority_updates: Details of priority changes
        - effectiveness_metrics: Learning effectiveness metrics
    
    Requirements covered: 8.10
    """
    from app.services.learning_pipeline_service import LearningPipelineService
    
    try:
        learning_service = LearningPipelineService(db)
        
        # Trigger batch update for single user
        update_result = learning_service.trigger_batch_learning_update([current_user.id])
        
        # Get user-specific result
        user_result = None
        for result in update_result.get("user_results", []):
            if result.get("user_id") == current_user.id:
                user_result = result
                break
        
        if not user_result:
            raise HTTPException(
                status_code=404,
                detail="No learning update result found for user"
            )
        
        return {
            "user_id": current_user.id,
            "update_result": user_result,
            "batch_info": {
                "total_users": update_result.get("total_users", 0),
                "successful_updates": update_result.get("successful_updates", 0),
                "failed_updates": update_result.get("failed_updates", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error triggering learning update: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger learning update: {str(e)}"
        )
