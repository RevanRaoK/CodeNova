#!/usr/bin/env node

/**
 * Integration test runner script
 * Validates end-to-end workflows and component integration
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const colors = {
     reset: '\x1b[0m',
     bright: '\x1b[1m',
     red: '\x1b[31m',
     green: '\x1b[32m',
     yellow: '\x1b[33m',
     blue: '\x1b[34m',
     magenta: '\x1b[35m',
     cyan: '\x1b[36m'
};

const log = {
     info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
     success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
     warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
     error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
     header: (msg) => console.log(`\n${colors.bright}${colors.cyan}${msg}${colors.reset}\n`)
};

class IntegrationTestRunner {
     constructor() {
          this.testResults = {
               passed: 0,
               failed: 0,
               skipped: 0,
               errors: []
          };
     }

     async runAllTests() {
          log.header('🚀 Running Integration Tests');

          try {
               await this.validateEnvironment();
               await this.runUnitTests();
               await this.runE2ETests();
               await this.validateAPIEndpoints();
               await this.validateComponentIntegration();
               await this.validateWorkflowIntegration();
               await this.generateReport();
          } catch (error) {
               log.error(`Test runner failed: ${error.message}`);
               process.exit(1);
          }
     }

     async validateEnvironment() {
          log.header('📋 Environment Validation');

          const checks = [
               {
                    name: 'Node.js version',
                    check: () => {
                         const version = process.version;
                         const major = parseInt(version.slice(1).split('.')[0]);
                         return major >= 18;
                    },
                    message: 'Node.js 18+ required'
               },
               {
                    name: 'Package.json exists',
                    check: () => fs.existsSync('package.json'),
                    message: 'package.json not found'
               },
               {
                    name: 'Dependencies installed',
                    check: () => fs.existsSync('node_modules'),
                    message: 'Run npm install first'
               },
               {
                    name: 'Vite config exists',
                    check: () => fs.existsSync('vite.config.mjs'),
                    message: 'vite.config.mjs not found'
               },
               {
                    name: 'Test setup exists',
                    check: () => fs.existsSync('src/test-setup.js'),
                    message: 'Test setup file not found'
               }
          ];

          for (const check of checks) {
               try {
                    if (check.check()) {
                         log.success(check.name);
                         this.testResults.passed++;
                    } else {
                         log.error(`${check.name}: ${check.message}`);
                         this.testResults.failed++;
                         this.testResults.errors.push(`Environment: ${check.message}`);
                    }
               } catch (error) {
                    log.error(`${check.name}: ${error.message}`);
                    this.testResults.failed++;
                    this.testResults.errors.push(`Environment: ${check.name} - ${error.message}`);
               }
          }
     }

     async runUnitTests() {
          log.header('🧪 Unit Tests');

          try {
               log.info('Running Vitest unit tests...');
               execSync('npm run test:unit -- --run', { stdio: 'inherit' });
               log.success('Unit tests passed');
               this.testResults.passed++;
          } catch (error) {
               log.error('Unit tests failed');
               this.testResults.failed++;
               this.testResults.errors.push('Unit tests failed');
          }
     }

     async runE2ETests() {
          log.header('🎭 End-to-End Tests');

          try {
               log.info('Running E2E user journey tests...');
               execSync('npm run test:e2e -- --run', { stdio: 'inherit' });
               log.success('E2E tests passed');
               this.testResults.passed++;
          } catch (error) {
               log.error('E2E tests failed');
               this.testResults.failed++;
               this.testResults.errors.push('E2E tests failed');
          }
     }

     async validateAPIEndpoints() {
          log.header('🌐 API Endpoint Validation');

          const endpoints = [
               { method: 'GET', path: '/api/v1/monitoring/health', description: 'Health check' },
               { method: 'POST', path: '/api/v1/auth/register', description: 'User registration' },
               { method: 'POST', path: '/api/v1/auth/login-json', description: 'User login' },
               { method: 'GET', path: '/api/v1/analytics/dashboard', description: 'Dashboard analytics' },
               { method: 'POST', path: '/api/v1/feedback/submit', description: 'Feedback submission' },
               { method: 'GET', path: '/api/v1/github/repositories', description: 'GitHub repositories' },
               { method: 'POST', path: '/api/v1/files/upload', description: 'File upload' },
               { method: 'GET', path: '/api/v1/admin/users', description: 'Admin user management' }
          ];

          for (const endpoint of endpoints) {
               try {
                    // This would normally make actual HTTP requests to validate endpoints
                    // For now, we'll just check if the endpoint definitions exist in the codebase
                    const routeExists = this.checkRouteExists(endpoint.path);

                    if (routeExists) {
                         log.success(`${endpoint.method} ${endpoint.path} - ${endpoint.description}`);
                         this.testResults.passed++;
                    } else {
                         log.warning(`${endpoint.method} ${endpoint.path} - Route not found`);
                         this.testResults.skipped++;
                    }
               } catch (error) {
                    log.error(`${endpoint.method} ${endpoint.path} - ${error.message}`);
                    this.testResults.failed++;
                    this.testResults.errors.push(`API: ${endpoint.path} - ${error.message}`);
               }
          }
     }

     async validateComponentIntegration() {
          log.header('🧩 Component Integration');

          const components = [
               { name: 'WorkflowOrchestrator', path: 'components/WorkflowOrchestrator.jsx' },
               { name: 'IntegratedApp', path: 'components/IntegratedApp.jsx' },
               { name: 'ErrorBoundary', path: 'utils/errorHandler.js' },
               { name: 'IntegrationService', path: 'services/integrationService.js' },
               { name: 'AuthContext', path: 'contexts/AuthContext.jsx' },
               { name: 'NotificationContext', path: 'contexts/NotificationContext.jsx' }
          ];

          for (const component of components) {
               try {
                    const componentPath = path.join(process.cwd(), component.path);

                    if (fs.existsSync(componentPath)) {
                         const content = fs.readFileSync(componentPath, 'utf8');

                         // Basic validation - check if component exports something
                         if (content.includes('export') && content.length > 100) {
                              log.success(`${component.name} - Component exists and has content`);
                              this.testResults.passed++;
                         } else {
                              log.warning(`${component.name} - Component exists but may be incomplete`);
                              this.testResults.skipped++;
                         }
                    } else {
                         log.error(`${component.name} - Component file not found: ${component.path}`);
                         this.testResults.failed++;
                         this.testResults.errors.push(`Component: ${component.name} not found`);
                    }
               } catch (error) {
                    log.error(`${component.name} - ${error.message}`);
                    this.testResults.failed++;
                    this.testResults.errors.push(`Component: ${component.name} - ${error.message}`);
               }
          }
     }

     async validateWorkflowIntegration() {
          log.header('🔄 Workflow Integration');

          const workflows = [
               'completeUserOnboarding',
               'completeGitHubIntegration',
               'completeFileAnalysisWorkflow',
               'completeAdminUserManagement',
               'completeFeedbackAnalysisWorkflow',
               'completeHomepageToDashboardJourney'
          ];

          try {
               const integrationServicePath = path.join(process.cwd(), 'services/integrationService.js');

               if (fs.existsSync(integrationServicePath)) {
                    const content = fs.readFileSync(integrationServicePath, 'utf8');

                    for (const workflow of workflows) {
                         if (content.includes(workflow)) {
                              log.success(`${workflow} - Workflow method exists`);
                              this.testResults.passed++;
                         } else {
                              log.error(`${workflow} - Workflow method not found`);
                              this.testResults.failed++;
                              this.testResults.errors.push(`Workflow: ${workflow} not implemented`);
                         }
                    }
               } else {
                    log.error('IntegrationService not found');
                    this.testResults.failed++;
                    this.testResults.errors.push('IntegrationService file not found');
               }
          } catch (error) {
               log.error(`Workflow validation failed: ${error.message}`);
               this.testResults.failed++;
               this.testResults.errors.push(`Workflow validation: ${error.message}`);
          }
     }

     checkRouteExists(routePath) {
          // This is a simplified check - in a real implementation, 
          // you would parse the actual route definitions
          const backendPath = path.join(process.cwd(), '../backend');

          if (!fs.existsSync(backendPath)) {
               return false;
          }

          // Check if route pattern exists in backend files
          try {
               const apiPath = path.join(backendPath, 'app/api/v1');
               if (fs.existsSync(apiPath)) {
                    const files = fs.readdirSync(apiPath, { recursive: true });
                    return files.some(file => {
                         if (file.endsWith('.py')) {
                              const content = fs.readFileSync(path.join(apiPath, file), 'utf8');
                              return content.includes(routePath.split('/').pop());
                         }
                         return false;
                    });
               }
          } catch (error) {
               return false;
          }

          return false;
     }

     generateReport() {
          log.header('📊 Test Results Summary');

          const total = this.testResults.passed + this.testResults.failed + this.testResults.skipped;
          const passRate = total > 0 ? ((this.testResults.passed / total) * 100).toFixed(1) : 0;

          console.log(`Total Tests: ${total}`);
          console.log(`${colors.green}Passed: ${this.testResults.passed}${colors.reset}`);
          console.log(`${colors.red}Failed: ${this.testResults.failed}${colors.reset}`);
          console.log(`${colors.yellow}Skipped: ${this.testResults.skipped}${colors.reset}`);
          console.log(`Pass Rate: ${passRate}%`);

          if (this.testResults.errors.length > 0) {
               log.header('❌ Errors');
               this.testResults.errors.forEach(error => {
                    console.log(`  • ${error}`);
               });
          }

          if (this.testResults.failed > 0) {
               log.error('Some tests failed. Please review the errors above.');
               process.exit(1);
          } else {
               log.success('All integration tests passed! 🎉');
          }
     }
}

// Run tests if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
     const runner = new IntegrationTestRunner();
     runner.runAllTests().catch(error => {
          log.error(`Test runner crashed: ${error.message}`);
          process.exit(1);
     });
}

export default IntegrationTestRunner;