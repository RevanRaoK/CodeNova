-- Quick queries to check repository analyses

-- 1. View all repository analyses (pr_number = 0)
SELECT 
    id,
    repository_id,
    pr_title,
    status,
    issues_found,
    errors_count,
    warnings_count,
    started_at,
    completed_at,
    created_at,
    analysis_results
FROM pr_analyses 
WHERE pr_number = 0 
ORDER BY created_at DESC;

-- 2. Count analyses by status
SELECT 
    status,
    COUNT(*) as count
FROM pr_analyses 
WHERE pr_number = 0
GROUP BY status;

-- 3. View most recent repository analysis with details
SELECT 
    pa.id,
    pa.pr_title,
    pa.status,
    pa.issues_found,
    pa.created_at,
    pa.analysis_results,
    gr.repo_name,
    gr.repo_url
FROM pr_analyses pa
JOIN github_repositories gr ON pa.repository_id = gr.id
WHERE pa.pr_number = 0
ORDER BY pa.created_at DESC
LIMIT 1;

-- 4. View all analyses (both PR and repository) for a specific repository
-- Replace 'YOUR_REPO_ID' with actual repository ID
SELECT 
    id,
    CASE 
        WHEN pr_number = 0 THEN 'Full Repository Analysis'
        ELSE 'PR #' || pr_number
    END as analysis_type,
    pr_title,
    status,
    issues_found,
    created_at,
    completed_at
FROM pr_analyses 
WHERE repository_id = 'YOUR_REPO_ID'
ORDER BY created_at DESC;

-- 5. Check if analysis is stuck (pending for > 10 minutes)
SELECT 
    id,
    pr_title,
    status,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_pending
FROM pr_analyses 
WHERE pr_number = 0 
    AND status = 'pending'
    AND created_at < NOW() - INTERVAL '10 minutes'
ORDER BY created_at DESC;

-- 6. View analysis results JSON for latest analysis
SELECT 
    id,
    pr_title,
    status,
    analysis_results::text
FROM pr_analyses 
WHERE pr_number = 0 
ORDER BY created_at DESC
LIMIT 1;

-- 7. Manually mark an analysis as failed (for testing retry)
-- Replace 'ANALYSIS_ID' with actual analysis ID
-- UPDATE pr_analyses 
-- SET status = 'failed', 
--     error_message = 'Test failure for retry functionality'
-- WHERE id = 'ANALYSIS_ID';

-- 8. Delete test analyses (cleanup)
-- BE CAREFUL WITH THIS!
-- DELETE FROM pr_analyses WHERE pr_number = 0 AND status = 'pending';
