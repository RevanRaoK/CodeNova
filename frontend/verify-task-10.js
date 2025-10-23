#!/usr/bin/env node

/**
 * Verification script for Task 10 implementation
 * Checks that all required files exist and have proper structure
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const COLORS = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(message, color = 'reset') {
  console.log(`${COLORS[color]}${message}${COLORS.reset}`);
}

function checkFile(filePath, description) {
  const fullPath = path.join(__dirname, filePath);
  if (fs.existsSync(fullPath)) {
    log(`✓ ${description}`, 'green');
    return true;
  } else {
    log(`✗ ${description} - File not found: ${filePath}`, 'red');
    return false;
  }
}

function checkFileContent(filePath, searchStrings, description) {
  const fullPath = path.join(__dirname, filePath);
  if (!fs.existsSync(fullPath)) {
    log(`✗ ${description} - File not found: ${filePath}`, 'red');
    return false;
  }

  const content = fs.readFileSync(fullPath, 'utf8');
  const missing = searchStrings.filter(str => !content.includes(str));

  if (missing.length === 0) {
    log(`✓ ${description}`, 'green');
    return true;
  } else {
    log(`✗ ${description} - Missing: ${missing.join(', ')}`, 'red');
    return false;
  }
}

log('\n=== Task 10 Implementation Verification ===\n', 'blue');

let passed = 0;
let failed = 0;

// Check new components
log('Checking new components...', 'yellow');
if (checkFile('components/FileUploadIntegration.jsx', 'FileUploadIntegration component')) passed++; else failed++;
if (checkFile('components/FeedbackLearningIntegration.jsx', 'FeedbackLearningIntegration component')) passed++; else failed++;
if (checkFile('components/LoadingState.jsx', 'LoadingState component')) passed++; else failed++;
if (checkFile('pages/IntegrationDemo.jsx', 'IntegrationDemo page')) passed++; else failed++;

// Check modified files
log('\nChecking modified files...', 'yellow');
if (checkFile('src/App.tsx', 'App.tsx exists')) passed++; else failed++;
if (checkFile('components/ProtectedRoute.jsx', 'ProtectedRoute.jsx exists')) passed++; else failed++;
if (checkFile('components/AdminRouter.jsx', 'AdminRouter.jsx exists')) passed++; else failed++;
if (checkFile('components/Layout/Sidebar.jsx', 'Sidebar.jsx exists')) passed++; else failed++;

// Check routing updates
log('\nChecking routing updates...', 'yellow');
if (checkFileContent(
  'src/App.tsx',
  ['IntegrationDemo', '/integration-demo', '/analysis-history'],
  'App.tsx has new routes'
)) passed++; else failed++;

// Check ProtectedRoute enhancements
log('\nChecking ProtectedRoute enhancements...', 'yellow');
if (checkFileContent(
  'components/ProtectedRoute.jsx',
  ['allowedRoles', 'redirectTo', 'Loader2'],
  'ProtectedRoute has role-based access'
)) passed++; else failed++;

// Check Sidebar enhancements
log('\nChecking Sidebar enhancements...', 'yellow');
if (checkFileContent(
  'components/Layout/Sidebar.jsx',
  ['isAdmin', 'Administration', 'Analysis', '/analysis-history'],
  'Sidebar has role-based sections'
)) passed++; else failed++;

// Check AdminRouter updates
log('\nChecking AdminRouter updates...', 'yellow');
if (checkFileContent(
  'components/AdminRouter.jsx',
  ['ProtectedRoute', 'allowedRoles'],
  'AdminRouter uses enhanced ProtectedRoute'
)) passed++; else failed++;

// Check FileUploadIntegration
log('\nChecking FileUploadIntegration...', 'yellow');
if (checkFileContent(
  'components/FileUploadIntegration.jsx',
  ['uploadMultipleFiles', 'pollBatchStatus', 'onAnalysisComplete', 'autoNavigate'],
  'FileUploadIntegration has required features'
)) passed++; else failed++;

// Check FeedbackLearningIntegration
log('\nChecking FeedbackLearningIntegration...', 'yellow');
if (checkFileContent(
  'components/FeedbackLearningIntegration.jsx',
  ['accept', 'reject', 'modify', 'learningImpact', 'submitFeedback'],
  'FeedbackLearningIntegration has required features'
)) passed++; else failed++;

// Check LoadingState
log('\nChecking LoadingState...', 'yellow');
if (checkFileContent(
  'components/LoadingState.jsx',
  ['LoadingState', 'EmptyState', 'ErrorState', 'spinner', 'skeleton'],
  'LoadingState has all variants'
)) passed++; else failed++;

// Check documentation
log('\nChecking documentation...', 'yellow');
if (checkFile('ROUTING_NAVIGATION_GUIDE.md', 'Routing guide documentation')) passed++; else failed++;
if (checkFile('../TASK_10_IMPLEMENTATION_SUMMARY.md', 'Implementation summary')) passed++; else failed++;

// Summary
log('\n=== Verification Summary ===\n', 'blue');
log(`Passed: ${passed}`, 'green');
log(`Failed: ${failed}`, failed > 0 ? 'red' : 'green');

if (failed === 0) {
  log('\n✓ All checks passed! Task 10 implementation is complete.', 'green');
  process.exit(0);
} else {
  log('\n✗ Some checks failed. Please review the errors above.', 'red');
  process.exit(1);
}
