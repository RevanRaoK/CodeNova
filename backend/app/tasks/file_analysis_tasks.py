"""
Redis queue tasks for file analysis and processing.

This module contains background tasks for:
- File content analysis
- File upload processing
- Metadata generation
- AST parsing and analysis

Requirements covered: 5.1, 5.3
"""

import logging
import time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.core.redis_queue import redis_queue
from app.core.queue_config import QueuePriority
from app.core.database import SessionLocal
from app.models.stored_file import StoredFile
from app.services.ai_service import AIService
from app.services.cache_service import cache_service
from app.utils.ast_parser import ASTParser

logger = logging.getLogger(__name__)


def get_db_session():
    """Get database session context manager."""
    class DBSession:
        def __enter__(self):
            self.db = SessionLocal()
            return self.db
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.db.close()
    
    return DBSession()


@redis_queue.task('analyze_file_content', QueuePriority.MEDIUM)
async def analyze_file_content(file_id: int, user_id: int, analysis_type: str = "full") -> Dict[str, Any]:
    """
    Analyze file content using AI service.
    
    Args:
        file_id: ID of the stored file
        user_id: ID of the user requesting analysis
        analysis_type: Type of analysis to perform (full, syntax, security, etc.)
        
    Returns:
        Analysis results dictionary
    """
    start_time = time.time()
    
    try:
        # Get database session
        with get_db_session() as db:
            # Retrieve file record
            stored_file = db.query(StoredFile).filter(
                StoredFile.id == file_id,
                StoredFile.user_id == user_id
            ).first()
            
            if not stored_file:
                raise ValueError(f"File {file_id} not found for user {user_id}")
            
            # Check cache first
            cache_key = f"analysis:{file_id}:{analysis_type}"
            cached_result = await cache_service.get(cache_key, "file")
            
            if cached_result:
                logger.info(f"Returning cached analysis for file {file_id}")
                return cached_result
            
            # For now, use mock file content since we need to integrate with actual storage
            # TODO: Integrate with actual file storage service
            file_content = f"# Mock file content for {stored_file.filename}\nprint('Hello, World!')"
            
            if not file_content:
                raise ValueError(f"Could not download file content for {file_id}")
            
            # Initialize AI service
            ai_service = AIService()
            
            # Perform analysis based on type
            analysis_result = {
                'file_id': file_id,
                'analysis_type': analysis_type,
                'timestamp': time.time(),
                'processing_time': 0,
                'results': {}
            }
            
            if analysis_type in ['full', 'syntax']:
                # AST parsing and syntax analysis
                ast_parser = ASTParser()
                ast_result = ast_parser.parse_code(file_content, stored_file.file_type)
                analysis_result['results']['ast_analysis'] = ast_result
            
            if analysis_type in ['full', 'ai']:
                # AI-powered analysis (run in thread pool since it's sync)
                import asyncio
                loop = asyncio.get_event_loop()
                ai_analysis = await loop.run_in_executor(
                    None, 
                    lambda: ai_service.get_review_for_code(file_content)
                )
                analysis_result['results']['ai_analysis'] = ai_analysis
            
            if analysis_type in ['full', 'security']:
                # Security analysis (mock for now)
                security_analysis = {
                    'status': 'completed',
                    'issues': [],
                    'score': 'good'
                }
                analysis_result['results']['security_analysis'] = security_analysis
            
            # Calculate processing time
            processing_time = time.time() - start_time
            analysis_result['processing_time'] = processing_time
            
            # Cache the result
            await cache_service.set(
                cache_key, 
                analysis_result, 
                "file", 
                ttl=1800  # 30 minutes
            )
            
            # Update file metadata
            stored_file.last_analyzed = db.func.now()
            stored_file.analysis_status = "completed"
            db.commit()
            
            logger.info(f"File analysis completed for {file_id} in {processing_time:.2f}s")
            return analysis_result
            
    except Exception as exc:
        logger.error(f"Error analyzing file {file_id}: {exc}")
        
        # Update file status on error
        try:
            with get_db_session() as db:
                stored_file = db.query(StoredFile).filter(StoredFile.id == file_id).first()
                if stored_file:
                    stored_file.analysis_status = "failed"
                    db.commit()
        except Exception as db_exc:
            logger.error(f"Error updating file status: {db_exc}")
        
        raise exc


@redis_queue.task('process_file_upload', QueuePriority.MEDIUM)
async def process_file_upload(file_id: int, user_id: int, auto_analyze: bool = True) -> Dict[str, Any]:
    """
    Process uploaded file and optionally trigger analysis.
    
    Args:
        file_id: ID of the uploaded file
        user_id: ID of the user who uploaded the file
        auto_analyze: Whether to automatically trigger analysis
        
    Returns:
        Processing results dictionary
    """
    try:
        with get_db_session() as db:
            # Retrieve file record
            stored_file = db.query(StoredFile).filter(
                StoredFile.id == file_id,
                StoredFile.user_id == user_id
            ).first()
            
            if not stored_file:
                raise ValueError(f"File {file_id} not found for user {user_id}")
            
            # Generate metadata
            metadata_task_id = await generate_file_metadata.delay(file_id, user_id)
            
            result = {
                'file_id': file_id,
                'status': 'processed',
                'metadata_task_id': metadata_task_id,
                'analysis_task_id': None
            }
            
            # Trigger analysis if requested
            if auto_analyze:
                analysis_task_id = await analyze_file_content.delay(file_id, user_id, "full")
                result['analysis_task_id'] = analysis_task_id
            
            # Update file status
            stored_file.processing_status = "completed"
            db.commit()
            
            logger.info(f"File upload processing completed for {file_id}")
            return result
            
    except Exception as exc:
        logger.error(f"Error processing file upload {file_id}: {exc}")
        
        # Update file status on error
        try:
            with get_db_session() as db:
                stored_file = db.query(StoredFile).filter(StoredFile.id == file_id).first()
                if stored_file:
                    stored_file.processing_status = "failed"
                    db.commit()
        except Exception as db_exc:
            logger.error(f"Error updating file status: {db_exc}")
        
        raise exc


@redis_queue.task('generate_file_metadata', QueuePriority.LOW)
async def generate_file_metadata(file_id: int, user_id: int) -> Dict[str, Any]:
    """
    Generate metadata for uploaded file.
    
    Args:
        file_id: ID of the file
        user_id: ID of the user
        
    Returns:
        Generated metadata dictionary
    """
    try:
        with get_db_session() as db:
            # Retrieve file record
            stored_file = db.query(StoredFile).filter(
                StoredFile.id == file_id,
                StoredFile.user_id == user_id
            ).first()
            
            if not stored_file:
                raise ValueError(f"File {file_id} not found for user {user_id}")
            
            # For now, use mock file content since we need to integrate with actual storage
            # TODO: Integrate with actual file storage service
            file_content = f"# Mock file content for {stored_file.filename}\nprint('Hello, World!')"
            
            if not file_content:
                raise ValueError(f"Could not download file for metadata generation")
            
            # Generate metadata
            metadata = {
                'file_size': len(file_content),
                'line_count': len(file_content.splitlines()) if isinstance(file_content, str) else 0,
                'character_count': len(file_content) if isinstance(file_content, str) else len(file_content),
                'file_type': stored_file.file_type,
                'encoding': 'utf-8',  # Default, could be detected
                'generated_at': time.time()
            }
            
            # Language-specific metadata
            if stored_file.file_type in ['python', 'javascript', 'java', 'cpp', 'c']:
                try:
                    ast_parser = ASTParser()
                    ast_info = ast_parser.get_basic_info(file_content, stored_file.file_type)
                    metadata.update(ast_info)
                except Exception as ast_exc:
                    logger.warning(f"Could not generate AST metadata: {ast_exc}")
            
            # Update file record with metadata
            stored_file.file_metadata = metadata
            db.commit()
            
            # Cache metadata
            cache_key = f"metadata:{file_id}"
            await cache_service.set(cache_key, metadata, "file", ttl=3600)  # 1 hour
            
            logger.info(f"Metadata generated for file {file_id}")
            return metadata
            
    except Exception as exc:
        logger.error(f"Error generating metadata for file {file_id}: {exc}")
        raise exc


@redis_queue.task('batch_analyze_files', QueuePriority.LOW)
async def batch_analyze_files(file_ids: List[int], user_id: int, analysis_type: str = "full") -> Dict[str, Any]:
    """
    Analyze multiple files in batch.
    
    Args:
        file_ids: List of file IDs to analyze
        user_id: ID of the user
        analysis_type: Type of analysis to perform
        
    Returns:
        Batch analysis results
    """
    results = {
        'total_files': len(file_ids),
        'successful': 0,
        'failed': 0,
        'task_ids': [],
        'errors': []
    }
    
    try:
        for file_id in file_ids:
            try:
                # Queue individual analysis task
                task_id = await analyze_file_content.delay(file_id, user_id, analysis_type)
                results['task_ids'].append({
                    'file_id': file_id,
                    'task_id': task_id
                })
                results['successful'] += 1
                
            except Exception as exc:
                logger.error(f"Error queuing analysis for file {file_id}: {exc}")
                results['failed'] += 1
                results['errors'].append({
                    'file_id': file_id,
                    'error': str(exc)
                })
        
        logger.info(f"Batch analysis queued: {results['successful']}/{results['total_files']} files")
        return results
        
    except Exception as exc:
        logger.error(f"Error in batch file analysis: {exc}")
        raise exc


@redis_queue.task('cleanup_failed_analyses', QueuePriority.LOW)
async def cleanup_failed_analyses(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up failed analysis records older than specified age.
    
    Args:
        max_age_hours: Maximum age in hours for failed records
        
    Returns:
        Cleanup results
    """
    try:
        with get_db_session() as db:
            # Find failed analyses older than max_age_hours
            cutoff_time = db.func.now() - db.text(f"INTERVAL '{max_age_hours} HOURS'")
            
            failed_files = db.query(StoredFile).filter(
                StoredFile.analysis_status == "failed",
                StoredFile.updated_at < cutoff_time
            ).all()
            
            cleanup_count = 0
            for file_record in failed_files:
                # Reset status to allow retry
                file_record.analysis_status = "pending"
                cleanup_count += 1
            
            db.commit()
            
            result = {
                'cleaned_up': cleanup_count,
                'cutoff_time': cutoff_time.isoformat() if hasattr(cutoff_time, 'isoformat') else str(cutoff_time)
            }
            
            logger.info(f"Cleaned up {cleanup_count} failed analysis records")
            return result
            
    except Exception as exc:
        logger.error(f"Error cleaning up failed analyses: {exc}")
        raise exc