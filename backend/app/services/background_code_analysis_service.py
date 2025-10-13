"""
Background Code Analysis Service for asynchronous code analysis.

This service provides comprehensive background code analysis capabilities:
- Asynchronous code analysis worker
- Job queuing for file analysis tasks
- Analysis result caching system
- Analysis progress tracking and notifications

Requirements covered: 2.1, 2.6
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from app.services.background_job_service import (
    background_job_service,
    BackgroundJob,
    JobStatus,
    JobPriority,
    background_job
)
from app.services.ai_service import aiservice
from app.services.analysis_service import analysis_service
from app.services.cache_service import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of code analysis that can be performed."""
    QUICK = "quick"
    FULL = "full"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    COMPREHENSIVE = "comprehensive"


class AnalysisStatus(Enum):
    """Status of code analysis operations."""
    PENDING = "pending"
    QUEUED = "queued"
    ANALYZING = "analyzing"
    PROCESSING_AI = "processing_ai"
    CACHING_RESULTS = "caching_results"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AnalysisRequest:
    """Code analysis request data structure."""
    id: str
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    language: str = "unknown"
    analysis_type: AnalysisType = AnalysisType.FULL
    user_id: Optional[str] = None
    priority: JobPriority = JobPriority.NORMAL
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class AnalysisResult:
    """Code analysis result data structure."""
    analysis_id: str
    request: AnalysisRequest
    status: AnalysisStatus
    issues: List[Dict[str, Any]] = None
    suggestions: List[Dict[str, Any]] = None
    metrics: Dict[str, Any] = None
    ai_insights: List[Dict[str, Any]] = None
    summary: Dict[str, Any] = None
    processing_time: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.suggestions is None:
            self.suggestions = []
        if self.metrics is None:
            self.metrics = {}
        if self.ai_insights is None:
            self.ai_insights = []
        if self.summary is None:
            self.summary = {}
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['request']['analysis_type'] = self.request.analysis_type.value
        data['request']['priority'] = self.request.priority.value
        data['request']['created_at'] = self.request.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create result from dictionary."""
        # Convert request data
        request_data = data['request'].copy()
        request_data['analysis_type'] = AnalysisType(request_data['analysis_type'])
        request_data['priority'] = JobPriority(request_data['priority'])
        request_data['created_at'] = datetime.fromisoformat(request_data['created_at'])
        
        # Create request object
        request = AnalysisRequest(**request_data)
        
        # Convert timestamps
        started_at = datetime.fromisoformat(data['started_at']) if data.get('started_at') else None
        completed_at = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        
        return cls(
            analysis_id=data['analysis_id'],
            request=request,
            status=AnalysisStatus(data['status']),
            issues=data.get('issues', []),
            suggestions=data.get('suggestions', []),
            metrics=data.get('metrics', {}),
            ai_insights=data.get('ai_insights', []),
            summary=data.get('summary', {}),
            processing_time=data.get('processing_time', 0.0),
            started_at=started_at,
            completed_at=completed_at,
            error=data.get('error')
        )


class BackgroundCodeAnalysisService:
    """
    Background code analysis service with comprehensive analysis capabilities.
    
    Features:
    - Asynchronous code analysis processing
    - Multiple analysis types (quick, full, security, etc.)
    - AI-powered insights and suggestions
    - Result caching with intelligent TTL
    - Progress tracking and notifications
    - Batch analysis support
    - Performance monitoring
    """
    
    def __init__(self):
        self._analysis_cache: Dict[str, AnalysisResult] = {}
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        self._metrics = {
            'total_analyses': 0,
            'completed_analyses': 0,
            'failed_analyses': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_processing_time': 0.0,
            'avg_processing_time': 0.0
        }
    
    async def initialize(self):
        """Initialize the background code analysis service."""
        try:
            # Ensure background job service is initialized
            if not hasattr(background_job_service, 'redis_client') or background_job_service.redis_client is None:
                await background_job_service.initialize()
            
            # Ensure cache service is initialized
            if not hasattr(cache_service, '_is_connected') or not cache_service._is_connected:
                await cache_service.initialize()
            
            logger.info("Background code analysis service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize background code analysis service: {e}")
            raise
    
    async def queue_analysis(
        self,
        file_id: Optional[str] = None,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        language: str = "unknown",
        analysis_type: AnalysisType = AnalysisType.FULL,
        user_id: Optional[str] = None,
        priority: JobPriority = JobPriority.NORMAL,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Queue a code analysis job for background processing.
        
        Args:
            file_id: Optional file ID for database lookup
            file_path: Optional file path for analysis
            content: Optional direct content to analyze
            language: Programming language of the code
            analysis_type: Type of analysis to perform
            user_id: Optional user ID for tracking
            priority: Job priority level
            metadata: Additional metadata for the analysis
            
        Returns:
            Analysis ID for tracking
        """
        if not any([file_id, file_path, content]):
            raise ValueError("Must provide either file_id, file_path, or content")
        
        # Create analysis request
        analysis_id = str(uuid.uuid4())
        request = AnalysisRequest(
            id=analysis_id,
            file_id=file_id,
            file_path=file_path,
            content=content,
            language=language,
            analysis_type=analysis_type,
            user_id=user_id,
            priority=priority,
            metadata=metadata or {}
        )
        
        # Check cache first for identical analysis
        cache_key = self._generate_cache_key(request)
        cached_result = await self._get_cached_result(cache_key)
        
        if cached_result:
            logger.info(f"Analysis {analysis_id} found in cache")
            self._metrics['cache_hits'] += 1
            
            # Create new result with current analysis_id but cached data
            cached_result.analysis_id = analysis_id
            cached_result.request = request
            
            # Cache the result with new ID
            await self._cache_result(analysis_id, cached_result)
            
            return analysis_id
        
        self._metrics['cache_misses'] += 1
        
        # Create initial result entry
        result = AnalysisResult(
            analysis_id=analysis_id,
            request=request,
            status=AnalysisStatus.PENDING
        )
        
        # Cache the initial result
        await self._cache_result(analysis_id, result)
        
        # Queue background job
        job_id = await background_job_service.enqueue_job(
            job_name="code_analysis",
            args=[analysis_id],
            kwargs={},
            priority=priority,
            user_id=user_id,
            metadata={
                'analysis_type': analysis_type.value,
                'language': language,
                'file_id': file_id,
                'file_path': file_path
            },
            timeout=self._get_analysis_timeout(analysis_type)
        )
        
        # Update result with job information
        result.status = AnalysisStatus.QUEUED
        result.metadata.update(result.request.metadata.copy())
        result.metadata['job_id'] = job_id
        
        await self._cache_result(analysis_id, result)
        
        logger.info(f"Queued code analysis {analysis_id} (job: {job_id}, type: {analysis_type.value})")
        self._metrics['total_analyses'] += 1
        
        return analysis_id
    
    async def queue_batch_analysis(
        self,
        analysis_requests: List[Dict[str, Any]],
        batch_priority: JobPriority = JobPriority.NORMAL,
        user_id: Optional[str] = None
    ) -> str:
        """
        Queue multiple code analysis jobs as a batch.
        
        Args:
            analysis_requests: List of analysis request dictionaries
            batch_priority: Priority for the batch job
            user_id: Optional user ID for tracking
            
        Returns:
            Batch ID for tracking all analyses
        """
        batch_id = str(uuid.uuid4())
        analysis_ids = []
        
        # Queue individual analyses
        for request_data in analysis_requests:
            analysis_id = await self.queue_analysis(
                file_id=request_data.get('file_id'),
                file_path=request_data.get('file_path'),
                content=request_data.get('content'),
                language=request_data.get('language', 'unknown'),
                analysis_type=AnalysisType(request_data.get('analysis_type', 'full')),
                user_id=user_id,
                priority=batch_priority,
                metadata={
                    'batch_id': batch_id,
                    **request_data.get('metadata', {})
                }
            )
            analysis_ids.append(analysis_id)
        
        # Cache batch information
        batch_info = {
            'batch_id': batch_id,
            'analysis_ids': analysis_ids,
            'total_count': len(analysis_ids),
            'completed_count': 0,
            'failed_count': 0,
            'created_at': datetime.utcnow().isoformat(),
            'user_id': user_id
        }
        
        await cache_service.set(
            f"batch:{batch_id}",
            batch_info,
            cache_type="analysis_batches",
            ttl=86400  # 24 hours
        )
        
        logger.info(f"Queued batch analysis {batch_id} with {len(analysis_ids)} analyses")
        return batch_id
    
    async def get_analysis_status(self, analysis_id: str) -> Optional[AnalysisResult]:
        """
        Get the current status and results of an analysis.
        
        Args:
            analysis_id: Analysis ID to query
            
        Returns:
            AnalysisResult or None if not found
        """
        return await self._get_cached_result(analysis_id)
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a batch analysis.
        
        Args:
            batch_id: Batch ID to query
            
        Returns:
            Batch status information or None if not found
        """
        batch_info = await cache_service.get(
            f"batch:{batch_id}",
            cache_type="analysis_batches"
        )
        
        if not batch_info:
            return None
        
        # Get status of individual analyses
        analysis_statuses = []
        completed_count = 0
        failed_count = 0
        
        for analysis_id in batch_info['analysis_ids']:
            result = await self.get_analysis_status(analysis_id)
            if result:
                status_info = {
                    'analysis_id': analysis_id,
                    'status': result.status.value,
                    'file_path': result.request.file_path,
                    'language': result.request.language,
                    'processing_time': result.processing_time
                }
                
                if result.status == AnalysisStatus.COMPLETED:
                    completed_count += 1
                    status_info['issues_count'] = len(result.issues)
                    status_info['suggestions_count'] = len(result.suggestions)
                elif result.status == AnalysisStatus.FAILED:
                    failed_count += 1
                    status_info['error'] = result.error
                
                analysis_statuses.append(status_info)
        
        # Update batch info
        batch_info['completed_count'] = completed_count
        batch_info['failed_count'] = failed_count
        batch_info['analysis_statuses'] = analysis_statuses
        batch_info['progress_percentage'] = (
            (completed_count + failed_count) / batch_info['total_count'] * 100
            if batch_info['total_count'] > 0 else 0
        )
        
        return batch_info
    
    async def cancel_analysis(self, analysis_id: str) -> bool:
        """
        Cancel a queued or running analysis.
        
        Args:
            analysis_id: Analysis ID to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        result = await self.get_analysis_status(analysis_id)
        
        if not result:
            return False
        
        if result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
            return False  # Cannot cancel finished analyses
        
        # Try to cancel the background job
        job_id = result.metadata.get('job_id')
        if job_id:
            await background_job_service.cancel_job(job_id)
        
        # Update analysis status
        result.status = AnalysisStatus.CANCELLED
        result.completed_at = datetime.utcnow()
        result.error = "Analysis cancelled by user"
        
        await self._cache_result(analysis_id, result)
        
        logger.info(f"Analysis {analysis_id} cancelled")
        return True
    
    async def get_user_analyses(
        self,
        user_id: str,
        status_filter: Optional[AnalysisStatus] = None,
        limit: int = 50
    ) -> List[AnalysisResult]:
        """
        Get analyses for a specific user.
        
        Args:
            user_id: User ID to query
            status_filter: Optional status filter
            limit: Maximum number of analyses to return
            
        Returns:
            List of user's analyses
        """
        # This would typically query a database, but for now we'll use cache patterns
        # In a production system, you'd want to maintain user analysis indexes
        
        user_analyses = []
        
        # Get user's background jobs and extract analysis IDs
        user_jobs = await background_job_service.get_user_jobs(user_id, limit=limit)
        
        for job in user_jobs:
            if job.name == "code_analysis" and job.args:
                analysis_id = job.args[0]
                result = await self.get_analysis_status(analysis_id)
                
                if result and (status_filter is None or result.status == status_filter):
                    user_analyses.append(result)
        
        return user_analyses
    
    async def get_analysis_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive analysis metrics and statistics.
        
        Returns:
            Dictionary containing analysis metrics
        """
        # Update average processing time
        if self._metrics['completed_analyses'] > 0:
            self._metrics['avg_processing_time'] = (
                self._metrics['total_processing_time'] / self._metrics['completed_analyses']
            )
        
        # Get cache statistics
        cache_info = await cache_service.get_cache_info()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'analysis_metrics': self._metrics.copy(),
            'cache_metrics': cache_info.get('cache_metrics', {}),
            'queue_metrics': await background_job_service.get_queue_statistics()
        }
    
    def add_progress_callback(self, analysis_id: str, callback: Callable):
        """Add a callback function for analysis progress updates."""
        if analysis_id not in self._progress_callbacks:
            self._progress_callbacks[analysis_id] = []
        self._progress_callbacks[analysis_id].append(callback)
    
    def remove_progress_callback(self, analysis_id: str, callback: Callable):
        """Remove a progress callback for an analysis."""
        if analysis_id in self._progress_callbacks:
            try:
                self._progress_callbacks[analysis_id].remove(callback)
                if not self._progress_callbacks[analysis_id]:
                    del self._progress_callbacks[analysis_id]
            except ValueError:
                pass
    
    async def _perform_analysis(self, analysis_id: str):
        """
        Perform the actual code analysis (called by background job).
        
        Args:
            analysis_id: Analysis ID to process
        """
        start_time = time.time()
        
        try:
            # Get analysis request
            result = await self.get_analysis_status(analysis_id)
            if not result:
                raise ValueError(f"Analysis {analysis_id} not found")
            
            # Update status
            result.status = AnalysisStatus.ANALYZING
            result.started_at = datetime.utcnow()
            await self._cache_result(analysis_id, result)
            await self._trigger_progress_callbacks(analysis_id, "Starting analysis", 10)
            
            # Get code content
            content = await self._get_code_content(result.request)
            if not content:
                raise ValueError("Could not retrieve code content")
            
            await self._trigger_progress_callbacks(analysis_id, "Content retrieved", 20)
            
            # Perform basic analysis
            basic_analysis = await analysis_service.analyze_code_content(
                content=content,
                filename=result.request.file_path or "unknown",
                language=result.request.language
            )
            
            result.issues = basic_analysis.get('issues', [])
            result.metrics = basic_analysis.get('metadata', {})
            
            await self._trigger_progress_callbacks(analysis_id, "Basic analysis complete", 50)
            
            # Perform AI analysis if enabled and requested
            if self._should_use_ai_analysis(result.request.analysis_type):
                result.status = AnalysisStatus.PROCESSING_AI
                await self._cache_result(analysis_id, result)
                await self._trigger_progress_callbacks(analysis_id, "Running AI analysis", 60)
                
                ai_suggestions = await aiservice.get_review_for_code_with_ast(
                    code=content,
                    language=result.request.language,
                    analysis_id=analysis_id
                )
                
                result.ai_insights = ai_suggestions
                result.suggestions = self._extract_suggestions(ai_suggestions)
                
                await self._trigger_progress_callbacks(analysis_id, "AI analysis complete", 80)
            
            # Generate summary
            result.summary = self._generate_analysis_summary(result)
            
            await self._trigger_progress_callbacks(analysis_id, "Caching results", 90)
            
            # Cache results
            result.status = AnalysisStatus.CACHING_RESULTS
            await self._cache_result(analysis_id, result)
            
            # Final completion
            result.status = AnalysisStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.processing_time = time.time() - start_time
            
            await self._cache_result(analysis_id, result)
            await self._trigger_progress_callbacks(analysis_id, "Analysis completed", 100)
            
            # Update metrics
            self._metrics['completed_analyses'] += 1
            self._metrics['total_processing_time'] += result.processing_time
            
            logger.info(f"Analysis {analysis_id} completed in {result.processing_time:.2f}s")
            
        except Exception as e:
            # Handle analysis failure
            error_msg = str(e)
            logger.error(f"Analysis {analysis_id} failed: {error_msg}")
            
            result = await self.get_analysis_status(analysis_id)
            if result:
                result.status = AnalysisStatus.FAILED
                result.completed_at = datetime.utcnow()
                result.error = error_msg
                result.processing_time = time.time() - start_time
                
                await self._cache_result(analysis_id, result)
            
            self._metrics['failed_analyses'] += 1
            raise
    
    async def _get_code_content(self, request: AnalysisRequest) -> Optional[str]:
        """Get code content from various sources."""
        if request.content:
            return request.content
        
        if request.file_path:
            try:
                # In a real implementation, this would read from file storage
                # For now, return a placeholder
                return f"# Code content from {request.file_path}\n# This would be actual file content"
            except Exception as e:
                logger.error(f"Failed to read file {request.file_path}: {e}")
                return None
        
        if request.file_id:
            try:
                # In a real implementation, this would query the database for file content
                # For now, return a placeholder
                return f"# Code content for file ID {request.file_id}\n# This would be actual file content"
            except Exception as e:
                logger.error(f"Failed to get content for file ID {request.file_id}: {e}")
                return None
        
        return None
    
    def _should_use_ai_analysis(self, analysis_type: AnalysisType) -> bool:
        """Determine if AI analysis should be used for the given analysis type."""
        ai_analysis_types = {
            AnalysisType.FULL,
            AnalysisType.COMPREHENSIVE,
            AnalysisType.PERFORMANCE,
            AnalysisType.STYLE
        }
        return analysis_type in ai_analysis_types and settings.GEMINI_API_KEY
    
    def _extract_suggestions(self, ai_insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract actionable suggestions from AI insights."""
        suggestions = []
        
        for insight in ai_insights:
            if insight.get('severity') in ['suggestion', 'info']:
                suggestions.append({
                    'type': 'improvement',
                    'message': insight.get('comment', ''),
                    'line': insight.get('line_number'),
                    'file': insight.get('file_path'),
                    'priority': 'low'
                })
        
        return suggestions
    
    def _generate_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Generate a comprehensive analysis summary."""
        total_issues = len(result.issues)
        total_suggestions = len(result.suggestions)
        
        # Count issues by severity
        severity_counts = {}
        for issue in result.issues:
            severity = issue.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(result)
        
        return {
            'total_issues': total_issues,
            'total_suggestions': total_suggestions,
            'severity_breakdown': severity_counts,
            'quality_score': quality_score,
            'analysis_type': result.request.analysis_type.value,
            'language': result.request.language,
            'processing_time': result.processing_time,
            'has_ai_insights': len(result.ai_insights) > 0,
            'metrics': result.metrics
        }
    
    def _calculate_quality_score(self, result: AnalysisResult) -> float:
        """Calculate a quality score based on analysis results."""
        base_score = 100.0
        
        # Deduct points for issues based on severity
        severity_weights = {
            'critical': 20,
            'high': 15,
            'error': 15,
            'medium': 10,
            'warning': 10,
            'low': 5,
            'info': 2,
            'suggestion': 1
        }
        
        for issue in result.issues:
            severity = issue.get('severity', 'unknown')
            weight = severity_weights.get(severity, 5)
            base_score -= weight
        
        # Ensure score doesn't go below 0
        return max(0.0, base_score)
    
    def _get_analysis_timeout(self, analysis_type: AnalysisType) -> int:
        """Get timeout for analysis based on type."""
        timeouts = {
            AnalysisType.QUICK: 60,      # 1 minute
            AnalysisType.FULL: 300,      # 5 minutes
            AnalysisType.SECURITY: 180,  # 3 minutes
            AnalysisType.PERFORMANCE: 240,  # 4 minutes
            AnalysisType.STYLE: 120,     # 2 minutes
            AnalysisType.COMPREHENSIVE: 600  # 10 minutes
        }
        return timeouts.get(analysis_type, 300)
    
    def _generate_cache_key(self, request: AnalysisRequest) -> str:
        """Generate a cache key for an analysis request."""
        # Create a hash based on content, language, and analysis type
        import hashlib
        
        content_hash = ""
        if request.content:
            content_hash = hashlib.md5(request.content.encode()).hexdigest()
        elif request.file_path:
            content_hash = hashlib.md5(request.file_path.encode()).hexdigest()
        elif request.file_id:
            content_hash = hashlib.md5(request.file_id.encode()).hexdigest()
        
        cache_components = [
            content_hash,
            request.language,
            request.analysis_type.value
        ]
        
        cache_string = "|".join(cache_components)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def _get_cached_result(self, key: str) -> Optional[AnalysisResult]:
        """Get analysis result from cache."""
        try:
            cached_data = await cache_service.get(key, cache_type="code_analysis")
            
            if cached_data:
                return AnalysisResult.from_dict(cached_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result for {key}: {e}")
            return None
    
    async def _cache_result(self, analysis_id: str, result: AnalysisResult):
        """Cache analysis result."""
        try:
            # Cache with analysis ID
            await cache_service.set(
                analysis_id,
                result.to_dict(),
                cache_type="code_analysis",
                ttl=3600  # 1 hour for active analyses
            )
            
            # Also cache with content hash for deduplication
            if result.status == AnalysisStatus.COMPLETED:
                cache_key = self._generate_cache_key(result.request)
                await cache_service.set(
                    cache_key,
                    result.to_dict(),
                    cache_type="code_analysis",
                    ttl=86400  # 24 hours for completed analyses
                )
            
        except Exception as e:
            logger.error(f"Error caching result for {analysis_id}: {e}")
    
    async def _trigger_progress_callbacks(self, analysis_id: str, message: str, percentage: float):
        """Trigger progress callbacks for an analysis."""
        if analysis_id in self._progress_callbacks:
            for callback in self._progress_callbacks[analysis_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(analysis_id, message, percentage)
                    else:
                        callback(analysis_id, message, percentage)
                except Exception as e:
                    logger.error(f"Progress callback failed for analysis {analysis_id}: {e}")


# Global background code analysis service instance
background_code_analysis_service = BackgroundCodeAnalysisService()


# Background job handler for code analysis
@background_job("code_analysis")
async def code_analysis_job(job_id: str, analysis_id: str):
    """Background job handler for code analysis."""
    try:
        await background_job_service.update_job_progress(
            job_id,
            current_step=1,
            total_steps=5,
            message="Starting code analysis"
        )
        
        # Perform the analysis
        await background_code_analysis_service._perform_analysis(analysis_id)
        
        await background_job_service.update_job_progress(
            job_id,
            current_step=5,
            total_steps=5,
            message="Code analysis completed"
        )
        
        # Get final result for job completion
        result = await background_code_analysis_service.get_analysis_status(analysis_id)
        
        job_result = {
            "analysis_id": analysis_id,
            "status": result.status.value if result else "unknown",
            "processing_time": result.processing_time if result else 0,
            "issues_count": len(result.issues) if result else 0,
            "suggestions_count": len(result.suggestions) if result else 0
        }
        
        await background_job_service.complete_job(job_id, job_result)
        
    except Exception as e:
        await background_job_service.fail_job(job_id, str(e))
        raise


# Utility functions for easy access
async def queue_code_analysis(
    content: str,
    language: str = "unknown",
    analysis_type: str = "full",
    user_id: Optional[str] = None
) -> str:
    """
    Utility function to queue a code analysis.
    
    Args:
        content: Code content to analyze
        language: Programming language
        analysis_type: Type of analysis ("quick", "full", etc.)
        user_id: Optional user ID
        
    Returns:
        Analysis ID for tracking
    """
    return await background_code_analysis_service.queue_analysis(
        content=content,
        language=language,
        analysis_type=AnalysisType(analysis_type),
        user_id=user_id
    )


async def get_analysis_result(analysis_id: str) -> Optional[Dict[str, Any]]:
    """
    Utility function to get analysis results.
    
    Args:
        analysis_id: Analysis ID to query
        
    Returns:
        Analysis result dictionary or None
    """
    result = await background_code_analysis_service.get_analysis_status(analysis_id)
    return result.to_dict() if result else None


async def initialize_background_code_analysis_service():
    """Initialize the background code analysis service."""
    await background_code_analysis_service.initialize()