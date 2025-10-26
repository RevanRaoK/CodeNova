"""
File analysis tasks for the queue system.

This module contains tasks related to file analysis and processing,
integrated with the background code analysis service.

Requirements covered: 2.1, 2.6
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio
import fnmatch
from datetime import datetime

from github import Github, GithubException
from sqlalchemy import select, update

from app.core.redis_queue import redis_queue
from app.core.hybrid_queue import hybrid_queue
from app.core.queue_config import QueuePriority
from app.core.database import AsyncSessionLocal
from app.models.github_integration import GitHubRepository, PRAnalysis, AnalysisStatus
from app.services.background_code_analysis_service import (
    background_code_analysis_service,
    AnalysisType,
    AnalysisStatus as BgAnalysisStatus
)
from app.services.ai_service import AIService
from app.core.json_encoder import sanitize_for_json

logger = logging.getLogger(__name__)


@redis_queue.task("analyze_file", priority=QueuePriority.MEDIUM)
@hybrid_queue.task("analyze_file", priority=QueuePriority.MEDIUM)
async def analyze_file(
    file_id: str, 
    file_path: str, 
    analysis_type: str = "full",
    language: str = "unknown",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a file for code quality, security issues, and suggestions.
    Uses the background code analysis service for comprehensive analysis.
    
    Args:
        file_id: Unique identifier for the file
        file_path: Path to the file to analyze
        analysis_type: Type of analysis to perform ("full", "quick", "security")
        language: Programming language of the file
        user_id: Optional user ID for tracking
    
    Returns:
        Analysis results dictionary
    """
    logger.info(f"Starting file analysis for {file_id} ({analysis_type})")
    
    try:
        # Queue analysis with background service
        analysis_id = await background_code_analysis_service.queue_analysis(
            file_id=file_id,
            file_path=file_path,
            language=language,
            analysis_type=AnalysisType(analysis_type),
            user_id=user_id,
            metadata={
                'source': 'file_analysis_task',
                'original_file_id': file_id
            }
        )
        
        # Wait for analysis completion with timeout
        timeout = 300  # 5 minutes
        start_time = asyncio.get_event_loop().time()
        
        while True:
            result = await background_code_analysis_service.get_analysis_status(analysis_id)
            
            if not result:
                raise Exception(f"Analysis {analysis_id} not found")
            
            if result.status == AnalysisStatus.COMPLETED:
                logger.info(f"File analysis completed for {file_id}")
                return {
                    "analysis_id": analysis_id,
                    "file_id": file_id,
                    "file_path": file_path,
                    "analysis_type": analysis_type,
                    "status": "completed",
                    "issues": result.issues,
                    "suggestions": result.suggestions,
                    "ai_insights": result.ai_insights,
                    "metrics": result.metrics,
                    "summary": result.summary,
                    "processing_time": result.processing_time
                }
            
            elif result.status == AnalysisStatus.FAILED:
                error_msg = result.error or "Analysis failed"
                logger.error(f"File analysis failed for {file_id}: {error_msg}")
                raise Exception(error_msg)
            
            elif result.status == AnalysisStatus.CANCELLED:
                logger.warning(f"File analysis cancelled for {file_id}")
                raise Exception("Analysis was cancelled")
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.error(f"File analysis timed out for {file_id}")
                await background_code_analysis_service.cancel_analysis(analysis_id)
                raise Exception("Analysis timed out")
            
            # Wait before checking again
            await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"File analysis failed for {file_id}: {e}")
        raise


@redis_queue.task("batch_analyze_files", priority=QueuePriority.LOW)
@hybrid_queue.task("batch_analyze_files", priority=QueuePriority.LOW)
async def batch_analyze_files(
    file_data: List[Dict[str, Any]], 
    analysis_type: str = "quick",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze multiple files in batch for efficiency.
    Uses the background code analysis service for batch processing.
    
    Args:
        file_data: List of file data dictionaries with file_id, file_path, language
        analysis_type: Type of analysis to perform
        user_id: Optional user ID for tracking
    
    Returns:
        Batch analysis results
    """
    logger.info(f"Starting batch analysis for {len(file_data)} files")
    
    try:
        # Prepare analysis requests
        analysis_requests = []
        for file_info in file_data:
            request = {
                'file_id': file_info.get('file_id'),
                'file_path': file_info.get('file_path'),
                'language': file_info.get('language', 'unknown'),
                'analysis_type': analysis_type,
                'metadata': {
                    'source': 'batch_analysis_task',
                    'original_file_id': file_info.get('file_id')
                }
            }
            analysis_requests.append(request)
        
        # Queue batch analysis
        batch_id = await background_code_analysis_service.queue_batch_analysis(
            analysis_requests=analysis_requests,
            user_id=user_id
        )
        
        # Wait for batch completion with timeout
        timeout = 600  # 10 minutes for batch
        start_time = asyncio.get_event_loop().time()
        
        while True:
            batch_status = await background_code_analysis_service.get_batch_status(batch_id)
            
            if not batch_status:
                raise Exception(f"Batch {batch_id} not found")
            
            total_files = batch_status['total_count']
            completed_files = batch_status['completed_count']
            failed_files = batch_status['failed_count']
            
            # Check if batch is complete
            if completed_files + failed_files >= total_files:
                logger.info(f"Batch analysis completed for {total_files} files")
                
                # Collect detailed results
                results = []
                total_issues = 0
                total_suggestions = 0
                
                for status_info in batch_status['analysis_statuses']:
                    result = {
                        "analysis_id": status_info['analysis_id'],
                        "file_path": status_info['file_path'],
                        "language": status_info['language'],
                        "status": status_info['status'],
                        "processing_time": status_info['processing_time']
                    }
                    
                    if status_info['status'] == 'completed':
                        result["issues_count"] = status_info.get('issues_count', 0)
                        result["suggestions_count"] = status_info.get('suggestions_count', 0)
                        total_issues += result["issues_count"]
                        total_suggestions += result["suggestions_count"]
                    elif status_info['status'] == 'failed':
                        result["error"] = status_info.get('error', 'Unknown error')
                    
                    results.append(result)
                
                return {
                    "batch_id": batch_id,
                    "total_files": total_files,
                    "completed_files": completed_files,
                    "failed_files": failed_files,
                    "results": results,
                    "summary": {
                        "total_issues": total_issues,
                        "total_suggestions": total_suggestions,
                        "success_rate": (completed_files / total_files * 100) if total_files > 0 else 0
                    },
                    "analysis_type": analysis_type
                }
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.error(f"Batch analysis timed out for batch {batch_id}")
                raise Exception("Batch analysis timed out")
            
            # Wait before checking again
            await asyncio.sleep(5)
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise


@redis_queue.task("generate_file_report", priority=QueuePriority.LOW)
@hybrid_queue.task("generate_file_report", priority=QueuePriority.LOW)
async def generate_file_report(analysis_results: Dict[str, Any], report_format: str = "json") -> Dict[str, Any]:
    """
    Generate a formatted report from analysis results.
    
    Args:
        analysis_results: Results from file analysis
        report_format: Format for the report ("json", "html", "pdf")
    
    Returns:
        Generated report information
    """
    logger.info(f"Generating {report_format} report for file analysis")
    
    try:
        # Simulate report generation
        await asyncio.sleep(1)
        
        report = {
            "report_id": f"report_{analysis_results.get('file_id', 'unknown')}",
            "format": report_format,
            "generated_at": "2024-01-01T00:00:00Z",
            "file_info": {
                "file_id": analysis_results.get("file_id"),
                "file_path": analysis_results.get("file_path")
            },
            "summary": {
                "total_issues": len(analysis_results.get("issues", [])),
                "severity_breakdown": {
                    "high": 0,
                    "medium": 1,
                    "low": 1
                }
            },
            "report_url": f"/reports/{analysis_results.get('file_id', 'unknown')}.{report_format}"
        }
        
        logger.info(f"Report generated successfully: {report['report_id']}")
        return report
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

@redis_queue.task("analyze_code_content", priority=QueuePriority.MEDIUM)
@hybrid_queue.task("analyze_code_content", priority=QueuePriority.MEDIUM)
async def analyze_code_content(
    content: str,
    language: str = "unknown",
    analysis_type: str = "full",
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze code content directly without file storage.
    
    Args:
        content: Code content to analyze
        language: Programming language
        analysis_type: Type of analysis to perform
        user_id: Optional user ID for tracking
        metadata: Optional metadata for the analysis
    
    Returns:
        Analysis results dictionary
    """
    logger.info(f"Starting content analysis ({analysis_type}, {language})")
    
    try:
        # Queue analysis with background service
        analysis_id = await background_code_analysis_service.queue_analysis(
            content=content,
            language=language,
            analysis_type=AnalysisType(analysis_type),
            user_id=user_id,
            metadata={
                'source': 'content_analysis_task',
                **(metadata or {})
            }
        )
        
        # Wait for analysis completion
        timeout = 300  # 5 minutes
        start_time = asyncio.get_event_loop().time()
        
        while True:
            result = await background_code_analysis_service.get_analysis_status(analysis_id)
            
            if not result:
                raise Exception(f"Analysis {analysis_id} not found")
            
            if result.status == AnalysisStatus.COMPLETED:
                logger.info(f"Content analysis completed: {analysis_id}")
                return {
                    "analysis_id": analysis_id,
                    "analysis_type": analysis_type,
                    "language": language,
                    "status": "completed",
                    "issues": result.issues,
                    "suggestions": result.suggestions,
                    "ai_insights": result.ai_insights,
                    "metrics": result.metrics,
                    "summary": result.summary,
                    "processing_time": result.processing_time
                }
            
            elif result.status == AnalysisStatus.FAILED:
                error_msg = result.error or "Analysis failed"
                logger.error(f"Content analysis failed: {error_msg}")
                raise Exception(error_msg)
            
            elif result.status == AnalysisStatus.CANCELLED:
                logger.warning(f"Content analysis cancelled: {analysis_id}")
                raise Exception("Analysis was cancelled")
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.error(f"Content analysis timed out: {analysis_id}")
                await background_code_analysis_service.cancel_analysis(analysis_id)
                raise Exception("Analysis timed out")
            
            # Wait before checking again
            await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise


@redis_queue.task("analyze_repository_files", priority=QueuePriority.LOW)
@hybrid_queue.task("analyze_repository_files", priority=QueuePriority.LOW)
async def analyze_repository_files(
    repository_id: str,
    file_patterns: List[str] = None,
    analysis_type: str = "comprehensive",
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze all files in a repository matching specified patterns using GitHub API.
    
    Args:
        repository_id: Repository ID to analyze
        file_patterns: List of file patterns to include (e.g., ["*.py", "*.js"])
        analysis_type: Type of analysis to perform
        user_id: Optional user ID for tracking
    
    Returns:
        Repository analysis results
    """
    logger.info(f"Starting repository analysis for {repository_id}")
    
    # CRITICAL: Convert any Pattern objects to strings immediately
    if file_patterns:
        file_patterns = [str(p) for p in file_patterns]
    
    async with AsyncSessionLocal() as db:
        try:
            # Get repository details from database
            repo_query = select(GitHubRepository).where(GitHubRepository.id == repository_id)
            repo_result = await db.execute(repo_query)
            repository = repo_result.scalar_one_or_none()
            
            if not repository:
                raise Exception(f"Repository {repository_id} not found")
            
            # Get analysis record
            analysis_query = select(PRAnalysis).where(
                PRAnalysis.repository_id == repository_id,
                PRAnalysis.pr_number == 0
            ).order_by(PRAnalysis.created_at.desc())
            analysis_result = await db.execute(analysis_query)
            analysis = analysis_result.scalars().first()
            
            if not analysis:
                raise Exception(f"Analysis record not found for repository {repository_id}")
            
            # Update status to in_progress
            analysis.status = AnalysisStatus.IN_PROGRESS
            analysis.started_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Fetching files from GitHub for {repository.repo_name}")
            
            # Initialize GitHub client with access token
            github_client = Github(login_or_token=repository.access_token)
            
            # Extract owner and repo name from repo_url or repo_name
            # Format: "owner/repo" or "https://github.com/owner/repo"
            if "/" in repository.repo_name:
                owner_repo = repository.repo_name
            else:
                # Parse from URL
                repo_url = repository.repo_url
                parts = repo_url.rstrip("/").split("/")
                owner_repo = f"{parts[-2]}/{parts[-1]}"
            
            repo = github_client.get_repo(owner_repo)
            
            # Get default branch
            default_branch = repo.default_branch
            branch = analysis.head_branch or default_branch
            
            logger.info(f"Scanning branch '{branch}' for files matching patterns: {file_patterns}")
            
            # Fetch repository file tree
            discovered_files = []
            
            try:
                contents = repo.get_contents("", ref=branch)
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        # Add directory contents to queue
                        contents.extend(repo.get_contents(file_content.path, ref=branch))
                    else:
                        # Check if file matches patterns
                        if _matches_patterns(file_content.path, file_patterns):
                            discovered_files.append({
                                "path": file_content.path,
                                "sha": file_content.sha,
                                "size": file_content.size,
                                "url": file_content.download_url
                            })
            
            except GithubException as e:
                logger.error(f"Failed to fetch repository contents: {e}")
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = f"Failed to fetch repository contents: {str(e)}"
                await db.commit()
                raise
            
            logger.info(f"Discovered {len(discovered_files)} files matching patterns")
            
            if not discovered_files:
                analysis.status = AnalysisStatus.COMPLETED
                analysis.completed_at = datetime.utcnow()
                results_dict = {
                    "status": "completed",
                    "message": "No files found matching patterns",
                    "total_files": 0,
                    "branch": branch,
                    "patterns": [str(p) for p in file_patterns] if file_patterns else []
                }
                analysis.analysis_results = sanitize_for_json(results_dict)
                await db.commit()
                return {
                    "repository_id": repository_id,
                    "status": "completed",
                    "message": "No files found matching patterns",
                    "total_files": 0
                }
            
            # Update progress
            results_dict = {
                "status": "discovering_files",
                "total_files": len(discovered_files),
                "files_discovered": len(discovered_files),
                "files_analyzed": 0,
                "branch": branch,
                "patterns": [str(p) for p in file_patterns] if file_patterns else [],
                "started_at": datetime.utcnow().isoformat()
            }
            analysis.analysis_results = sanitize_for_json(results_dict)
            await db.commit()
            
            # Initialize AI service
            ai_service = AIService()
            
            # Analyze files
            all_issues = []
            all_suggestions = []
            files_analyzed = 0
            files_failed = 0
            language_breakdown = {}
            
            for idx, file_info in enumerate(discovered_files):
                try:
                    logger.info(f"Analyzing file {idx + 1}/{len(discovered_files)}: {file_info['path']}")
                    
                    # Fetch file content
                    file_content_obj = repo.get_contents(file_info['path'], ref=branch)
                    
                    # Skip if file is too large (> 1MB)
                    if file_content_obj.size > 1024 * 1024:
                        logger.warning(f"Skipping large file: {file_info['path']} ({file_content_obj.size} bytes)")
                        files_failed += 1
                        continue
                    
                    # Decode content
                    try:
                        content = file_content_obj.decoded_content.decode('utf-8')
                    except UnicodeDecodeError:
                        logger.warning(f"Skipping binary file: {file_info['path']}")
                        files_failed += 1
                        continue
                    
                    # Detect language from file extension
                    language = _detect_language(file_info['path'])
                    language_breakdown[language] = language_breakdown.get(language, 0) + 1
                    
                    # Analyze with AI service
                    analysis_result = ai_service.analyze_code(
                        code=content,
                        language=language,
                        filename=file_info['path']
                    )
                    
                    # Extract issues and suggestions from AI result
                    # The result is a dictionary with 'issues' key
                    if analysis_result and 'issues' in analysis_result:
                        for item in analysis_result['issues']:
                            # Add file path to each item
                            item['file'] = file_info['path']
                            
                            # Normalize line number field
                            if 'line_number' in item:
                                item['line'] = item['line_number']
                            elif 'line' not in item:
                                item['line'] = 0
                            
                            # Add all findings to issues list
                            all_issues.append(item)
                    
                    files_analyzed += 1
                    
                    # Update progress every 5 files
                    if (idx + 1) % 5 == 0 or idx == len(discovered_files) - 1:
                        progress_percentage = ((idx + 1) / len(discovered_files)) * 100
                        # Rebuild analysis_results to avoid spreading Pattern objects
                        old_results = analysis.analysis_results or {}
                        results_dict = {
                            "status": "analyzing",
                            "total_files": old_results.get("total_files", len(discovered_files)),
                            "files_discovered": old_results.get("files_discovered", len(discovered_files)),
                            "files_analyzed": files_analyzed,
                            "files_failed": files_failed,
                            "progress_percentage": round(progress_percentage, 2),
                            "current_file": file_info['path'],
                            "branch": old_results.get("branch", branch),
                            "patterns": [str(p) for p in file_patterns] if file_patterns else [],
                            "started_at": old_results.get("started_at", datetime.utcnow().isoformat())
                        }
                        analysis.analysis_results = sanitize_for_json(results_dict)
                        await db.commit()
                    
                except Exception as file_error:
                    logger.error(f"Failed to analyze file {file_info['path']}: {file_error}")
                    files_failed += 1
                    continue
            
            # Count issues by severity
            errors_count = sum(1 for issue in all_issues if issue.get('severity') == 'error')
            warnings_count = sum(1 for issue in all_issues if issue.get('severity') == 'warning')
            
            # Update analysis with final results
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            analysis.issues_found = len(all_issues)
            analysis.errors_count = errors_count
            analysis.warnings_count = warnings_count
            
            # Build results dict
            results_dict = {
                "status": "completed",
                "branch": branch,
                "patterns": [str(p) for p in file_patterns] if file_patterns else [],
                "total_files": len(discovered_files),
                "files_analyzed": files_analyzed,
                "files_failed": files_failed,
                "progress_percentage": 100,
                "started_at": analysis.started_at.isoformat(),
                "completed_at": analysis.completed_at.isoformat(),
                "summary": {
                    "total_issues": len(all_issues),
                    "errors": errors_count,
                    "warnings": warnings_count,
                    "total_suggestions": len(all_suggestions),
                    "language_breakdown": language_breakdown,
                    "success_rate": round((files_analyzed / len(discovered_files)) * 100, 2) if discovered_files else 0
                },
                "issues": all_issues[:100],  # Store first 100 issues (to avoid JSON size limits)
                "suggestions": all_suggestions[:50],  # Store first 50 suggestions
                "has_more_issues": len(all_issues) > 100,
                "has_more_suggestions": len(all_suggestions) > 50
            }
            
            # CRITICAL: Sanitize the entire results dict to remove ANY Pattern objects
            analysis.analysis_results = sanitize_for_json(results_dict)
            
            await db.commit()
            
            logger.info(f"Repository analysis completed for {repository_id}: {files_analyzed} files analyzed, {len(all_issues)} issues found")
            
            return {
                "repository_id": repository_id,
                "status": "completed",
                "total_files": len(discovered_files),
                "files_analyzed": files_analyzed,
                "files_failed": files_failed,
                "total_issues": len(all_issues),
                "errors": errors_count,
                "warnings": warnings_count,
                "total_suggestions": len(all_suggestions)
            }
            
        except Exception as e:
            logger.error(f"Repository analysis failed for {repository_id}: {e}", exc_info=True)
            
            # Update analysis status to failed
            try:
                if analysis:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.completed_at = datetime.utcnow()
                    analysis.error_message = str(e)[:1000]
                    await db.commit()
            except:
                pass
            
            raise


def _matches_patterns(file_path: str, patterns: List[str] = None) -> bool:
    """
    Check if file path matches any of the given patterns.
    
    Args:
        file_path: Path to check
        patterns: List of glob patterns (e.g., ["*.py", "*.js"])
    
    Returns:
        True if matches any pattern, False otherwise
    """
    if not patterns:
        # Default patterns for common code files
        patterns = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cpp", "*.c", "*.go", "*.rs"]
    
    for pattern in patterns:
        if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(file_path, f"**/{pattern}"):
            return True
    
    return False


def _detect_language(file_path: str) -> str:
    """
    Detect programming language from file extension.
    
    Args:
        file_path: File path
    
    Returns:
        Language name
    """
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.cs': 'csharp'
    }
    
    ext = '.' + file_path.split('.')[-1] if '.' in file_path else ''
    return extension_map.get(ext.lower(), 'unknown')


@redis_queue.task("cache_analysis_results", priority=QueuePriority.LOW)
@hybrid_queue.task("cache_analysis_results", priority=QueuePriority.LOW)
async def cache_analysis_results(analysis_id: str, cache_duration: int = 3600) -> Dict[str, Any]:
    """
    Cache analysis results for faster future access.
    
    Args:
        analysis_id: Analysis ID to cache
        cache_duration: Cache duration in seconds
    
    Returns:
        Cache operation results
    """
    logger.info(f"Caching analysis results for {analysis_id}")
    
    try:
        # Get analysis result
        result = await background_code_analysis_service.get_analysis_status(analysis_id)
        
        if not result:
            raise Exception(f"Analysis {analysis_id} not found")
        
        if result.status != AnalysisStatus.COMPLETED:
            raise Exception(f"Analysis {analysis_id} is not completed")
        
        # Cache with extended TTL
        cache_key = f"extended_cache:{analysis_id}"
        success = await background_code_analysis_service._cache_result(cache_key, result)
        
        if success:
            logger.info(f"Analysis results cached for {analysis_id}")
            return {
                "analysis_id": analysis_id,
                "status": "cached",
                "cache_key": cache_key,
                "cache_duration": cache_duration
            }
        else:
            raise Exception("Failed to cache results")
        
    except Exception as e:
        logger.error(f"Failed to cache analysis results for {analysis_id}: {e}")
        raise


@redis_queue.task("cleanup_analysis_cache", priority=QueuePriority.LOW)
@hybrid_queue.task("cleanup_analysis_cache", priority=QueuePriority.LOW)
async def cleanup_analysis_cache(older_than_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old analysis results from cache.
    
    Args:
        older_than_hours: Remove cached results older than this many hours
    
    Returns:
        Cleanup operation results
    """
    logger.info(f"Cleaning up analysis cache (older than {older_than_hours} hours)")
    
    try:
        # This would typically scan cache keys and remove old entries
        # For now, we'll simulate the cleanup
        
        # In a real implementation, you would:
        # 1. Scan cache keys with pattern matching
        # 2. Check timestamps of cached results
        # 3. Remove entries older than threshold
        
        cleaned_count = 0  # Placeholder
        
        logger.info(f"Analysis cache cleanup completed: {cleaned_count} entries removed")
        
        return {
            "status": "completed",
            "cleaned_entries": cleaned_count,
            "threshold_hours": older_than_hours
        }
        
    except Exception as e:
        logger.error(f"Analysis cache cleanup failed: {e}")
        raise


# Utility task for monitoring analysis performance
@redis_queue.task("monitor_analysis_performance", priority=QueuePriority.LOW)
@hybrid_queue.task("monitor_analysis_performance", priority=QueuePriority.LOW)
async def monitor_analysis_performance() -> Dict[str, Any]:
    """
    Monitor and report analysis performance metrics.
    
    Returns:
        Performance metrics and statistics
    """
    logger.info("Monitoring analysis performance")
    
    try:
        # Get metrics from background code analysis service
        metrics = await background_code_analysis_service.get_analysis_metrics()
        
        # Add additional monitoring data
        performance_report = {
            "timestamp": metrics["timestamp"],
            "analysis_metrics": metrics["analysis_metrics"],
            "cache_performance": metrics["cache_metrics"],
            "queue_performance": metrics["queue_metrics"],
            "health_status": "healthy" if metrics["analysis_metrics"]["failed_analyses"] == 0 else "degraded"
        }
        
        logger.info("Analysis performance monitoring completed")
        return performance_report
        
    except Exception as e:
        logger.error(f"Analysis performance monitoring failed: {e}")
        raise