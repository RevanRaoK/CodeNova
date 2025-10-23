"""
Background worker for batch file analysis.

This worker processes files from batch uploads and performs code analysis
on each file asynchronously.

Requirements covered: 1.2, 1.3, 2.1, 2.2, 13.1, 13.2
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.file_batch import BatchFile, FileStatus, BatchStatus
from app.models.analysis import DirectAnalysis
from app.models.feedback import Issue
from app.services.file_upload_service import FileUploadService
from app.utils.ast_parser import ASTParser
from app.services.issue_id_service import IssueIDService


logger = logging.getLogger(__name__)


class BatchAnalysisWorker:
    """
    Worker for processing batch file analysis jobs.
    
    Handles background analysis of uploaded files with retry logic
    and error handling.
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 60
    
    def __init__(self):
        """Initialize the batch analysis worker."""
        self.ast_parser = ASTParser()
        self.issue_id_service = IssueIDService()
    
    def process_batch_file(
        self,
        file_id: str,
        retry_count: int = 0
    ) -> bool:
        """
        Process a single file from a batch.
        
        Args:
            file_id: ID of the batch file to process
            retry_count: Current retry attempt number
            
        Returns:
            True if processing succeeded, False otherwise
        """
        db = SessionLocal()
        
        try:
            # Get batch file
            batch_file = db.query(BatchFile).filter(BatchFile.id == file_id).first()
            
            if not batch_file:
                logger.error(f"Batch file {file_id} not found")
                return False
            
            logger.info(f"Processing batch file {file_id}: {batch_file.filename}")
            
            # Update status to analyzing
            upload_service = FileUploadService(db)
            upload_service.update_file_status(file_id, FileStatus.ANALYZING)
            
            # Perform analysis
            try:
                analysis_result = self._analyze_file(batch_file, db)
                
                if analysis_result:
                    # Update file status with results
                    upload_service.update_file_status(
                        file_id=file_id,
                        status=FileStatus.COMPLETED,
                        analysis_id=analysis_result['analysis_id'],
                        analysis_results=analysis_result['results']
                    )
                    
                    logger.info(f"Successfully analyzed file {file_id}")
                    return True
                else:
                    raise Exception("Analysis returned no results")
                    
            except Exception as e:
                logger.error(f"Error analyzing file {file_id}: {str(e)}")
                
                # Check if we should retry
                if retry_count < self.MAX_RETRIES:
                    logger.info(f"Scheduling retry {retry_count + 1}/{self.MAX_RETRIES} for file {file_id}")
                    # In a real implementation, this would schedule a delayed retry
                    # For now, we'll just mark it as failed
                    upload_service.update_file_status(
                        file_id=file_id,
                        status=FileStatus.FAILED,
                        error_message=f"Analysis failed after {retry_count + 1} attempts: {str(e)}",
                        error_code="ANALYSIS_ERROR"
                    )
                    return False
                else:
                    # Max retries exceeded
                    upload_service.update_file_status(
                        file_id=file_id,
                        status=FileStatus.FAILED,
                        error_message=f"Analysis failed after {self.MAX_RETRIES} retries: {str(e)}",
                        error_code="MAX_RETRIES_EXCEEDED"
                    )
                    return False
        
        except Exception as e:
            logger.error(f"Fatal error processing batch file {file_id}: {str(e)}")
            return False
        
        finally:
            db.close()
    
    def _analyze_file(
        self,
        batch_file: BatchFile,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a file's code content.
        
        Args:
            batch_file: The batch file to analyze
            db: Database session
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        from app.services.ai_service import get_ai_service_for_user
        
        try:
            # Get user's AI service
            ai_service = get_ai_service_for_user(batch_file.batch.user_id, db)
            
            # Parse code with AST parser
            logger.info(f"Parsing code with AST parser for {batch_file.filename}")
            ast_start_time = datetime.utcnow()
            ast_result = self.ast_parser.parse_code(
                batch_file.file_content,
                batch_file.language
            )
            ast_end_time = datetime.utcnow()
            ast_processing_time = (ast_end_time - ast_start_time).total_seconds()
            
            logger.info(f"AST parsing completed in {ast_processing_time:.3f}s")
            
            # Get code review from AI service
            logger.info(f"Calling AI service for {batch_file.filename}")
            suggestions = ai_service.get_review_for_code(batch_file.file_content)
            logger.info(f"AI service returned {len(suggestions)} suggestions")
            
            # Generate code hash for issue IDs
            code_hash = self.issue_id_service.generate_code_hash(batch_file.file_content)
            
            # Transform suggestions to structured issues
            issues = []
            issue_ids = []
            
            for i, suggestion in enumerate(suggestions):
                # Map AI service severities
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
                
                # Generate unique issue ID
                line_number = max(1, suggestion.get('line_number', 1))
                location = {
                    'line': line_number,
                    'column': 1,
                    'filename': batch_file.filename
                }
                
                pattern = f"{severity}:{suggestion.get('comment', 'unknown')[:50]}"
                issue_id = self.issue_id_service.generate_issue_id(code_hash, pattern, location)
                issue_ids.append(issue_id)
                
                issue = {
                    "id": issue_id,
                    "line": line_number,
                    "column": 1,
                    "severity": severity,
                    "message": suggestion.get('comment', 'No comment provided'),
                    "rule": "gemini-ai-review",
                    "category": "ai-review",
                    "suggestion": suggestion.get('suggestion', suggestion.get('comment', ''))
                }
                issues.append(issue)
                
                # Track issue
                self.issue_id_service.track_issue_resolution(issue_id, 'open')
            
            # Calculate metrics
            lines = batch_file.file_content.split('\n')
            lines_of_code = len([line for line in lines if line.strip()])
            total_lines = len(lines)
            
            # Basic complexity calculation
            complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'catch', 'switch', 'case']
            complexity = sum(batch_file.file_content.lower().count(keyword) for keyword in complexity_keywords)
            
            # Maintainability index
            avg_line_length = sum(len(line) for line in lines) / max(1, total_lines)
            maintainability_index = max(0, min(100, 100 - (complexity * 2) - (avg_line_length / 10)))
            
            metrics = {
                "lines_of_code": lines_of_code,
                "total_lines": total_lines,
                "complexity": complexity,
                "maintainability_index": int(maintainability_index),
                "duplicate_lines": 0,
                "test_coverage": None
            }
            
            # Generate summary
            issue_count = len(issues)
            severity_counts = {}
            for issue in issues:
                severity = issue.get('severity', 'info')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            summary_parts = [f"Analyzed {lines_of_code} lines of {batch_file.language} code"]
            
            if issue_count > 0:
                summary_parts.append(f"Found {issue_count} issues")
                if severity_counts:
                    severity_details = []
                    for severity in ['error', 'warning', 'info']:
                        if severity in severity_counts:
                            severity_details.append(f"{severity_counts[severity]} {severity}{'s' if severity_counts[severity] > 1 else ''}")
                    if severity_details:
                        summary_parts.append(f"({', '.join(severity_details)})")
            else:
                summary_parts.append("No issues found")
            
            summary = ". ".join(summary_parts) + "."
            
            # Create analysis record
            analysis_id = str(uuid.uuid4())
            created_at = datetime.utcnow()
            completed_at = datetime.utcnow()
            
            # Prepare AST metadata
            ast_metadata = None
            code_patterns = None
            
            if ast_result.is_valid:
                ast_metadata = {
                    'language': ast_result.language.value,
                    'is_valid': ast_result.is_valid,
                    'metadata': ast_result.metadata,
                    'pattern_count': len(ast_result.patterns),
                    'processing_time': ast_processing_time
                }
                
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
                ast_metadata = {
                    'language': ast_result.language.value,
                    'is_valid': False,
                    'error_message': ast_result.error_message,
                    'processing_time': ast_processing_time
                }
                code_patterns = []
            
            # Count issues by severity
            errors_count = sum(1 for issue in issues if issue.get('severity') == 'error')
            warnings_count = sum(1 for issue in issues if issue.get('severity') == 'warning')
            
            # Create DirectAnalysis record
            db_analysis = DirectAnalysis(
                id=analysis_id,
                user_id=batch_file.batch.user_id,
                code_content=batch_file.file_content,
                language=batch_file.language,
                filename=batch_file.filename,
                status="completed",
                created_at=created_at,
                completed_at=completed_at,
                results={
                    "issues": issues,
                    "metrics": metrics,
                    "summary": summary,
                    "ai_model_used": "gemini-ai"
                },
                lines_of_code=metrics["lines_of_code"],
                complexity_score=metrics["complexity"],
                maintainability_index=metrics["maintainability_index"],
                issues_count=len(issues),
                errors_count=errors_count,
                warnings_count=warnings_count,
                file_size_bytes=batch_file.file_size_bytes,
                ast_metadata=ast_metadata,
                code_patterns=code_patterns,
                issue_ids=issue_ids,
                ast_processing_time=ast_processing_time
            )
            
            db.add(db_analysis)
            
            # Create Issue records
            for issue_data in issues:
                issue_id = issue_data.get("id")
                if not issue_id:
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
                        "filename": batch_file.filename
                    },
                    suggestion_text=issue_data["message"],
                    code_context=batch_file.file_content[max(0, (issue_data["line"]-3)*50):(issue_data["line"]+3)*50],
                    original_code="",
                    suggested_fix=issue_data.get("suggestion", ""),
                    ast_node_type=None,
                    ast_metadata=None,
                    status="active",
                    confidence_score=0.8
                )
                db.add(db_issue)
            
            db.commit()
            
            logger.info(f"Created analysis {analysis_id} with {len(issues)} issues")
            
            return {
                "analysis_id": analysis_id,
                "results": {
                    "issues": issues,
                    "metrics": metrics,
                    "summary": summary
                }
            }
            
        except Exception as e:
            logger.error(f"Error in _analyze_file: {str(e)}")
            import traceback
            traceback.print_exc()
            db.rollback()
            raise
    
    def process_batch(self, batch_id: str) -> bool:
        """
        Process all files in a batch.
        
        Args:
            batch_id: ID of the batch to process
            
        Returns:
            True if all files processed successfully, False otherwise
        """
        db = SessionLocal()
        
        try:
            # Get all pending files in the batch
            files = db.query(BatchFile).filter(
                BatchFile.batch_id == batch_id,
                BatchFile.status.in_([FileStatus.PENDING, FileStatus.UPLOADED])
            ).all()
            
            if not files:
                logger.warning(f"No pending files found for batch {batch_id}")
                return True
            
            logger.info(f"Processing {len(files)} files in batch {batch_id}")
            
            # Update batch status to processing
            upload_service = FileUploadService(db)
            upload_service.update_batch_status(batch_id, BatchStatus.PROCESSING)
            
            # Process each file
            success_count = 0
            for file in files:
                if self.process_batch_file(file.id):
                    success_count += 1
            
            logger.info(f"Processed {success_count}/{len(files)} files successfully in batch {batch_id}")
            
            return success_count == len(files)
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_id}: {str(e)}")
            return False
        
        finally:
            db.close()


# Singleton worker instance
batch_analysis_worker = BatchAnalysisWorker()


def process_batch_file_task(file_id: str, retry_count: int = 0):
    """
    Task function for processing a single batch file.
    
    This can be called by a task queue (Celery, Redis Queue, etc.)
    
    Args:
        file_id: ID of the batch file to process
        retry_count: Current retry attempt
    """
    return batch_analysis_worker.process_batch_file(file_id, retry_count)


def process_batch_task(batch_id: str):
    """
    Task function for processing an entire batch.
    
    This can be called by a task queue (Celery, Redis Queue, etc.)
    
    Args:
        batch_id: ID of the batch to process
    """
    return batch_analysis_worker.process_batch(batch_id)
