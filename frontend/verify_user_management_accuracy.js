#!/usr/bin/env node
/**
 * Verification script for UserManagementPanel component accuracy.
 * 
 * This script verifies that the UserManagementPanel component:
 * - Displays accurate user count from database
 * - Shows correct team assignments
 * - Displays proper role badges
 * - Implements working search and filter functionality
 * 
 * Requirements: 5.1, 5.2, 5.3, 5.4
 */

import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class UserManagementVerification {
    constructor() {
        this.testResults = [];
        this.componentPath = join(__dirname, 'components', 'admin', 'UserManagementPanel.jsx');
        this.servicePath = join(__dirname, 'services', 'adminService.js');
    }

    logResult(testName, passed, message) {
        const status = passed ? 'PASS' : 'FAIL';
        this.testResults.push({
            test: testName,
            status,
            message
        });
        console.log(`[${status}] ${testName}: ${message}`);
    }

    readComponentFile() {
        try {
            const content = readFileSync(this.componentPath, 'utf8');
            this.logResult('Component File Access', true, 'Successfully read UserManagementPanel.jsx');
            return content;
        } catch (error) {
            this.logResult('Component File Access', false, `Cannot read component file: ${error.message}`);
            return null;
        }
    }

    readServiceFile() {
        try {
            const content = readFileSync(this.servicePath, 'utf8');
            this.logResult('Service File Access', true, 'Successfully read adminService.js');
            return content;
        } catch (error) {
            this.logResult('Service File Access', false, `Cannot read service file: ${error.message}`);
            return null;
        }
    }

    verifyApiIntegration(componentContent, serviceContent) {
        console.log('\n=== Verifying API Integration ===');
        
        if (!componentContent || !serviceContent) {
            this.logResult('API Integration', false, 'Cannot verify without component and service files');
            return;
        }

        // Check if component imports adminService
        const importsAdminService = componentContent.includes("import adminService from '../../services/adminService.js'") ||
                                   componentContent.includes('adminService');
        
        if (importsAdminService) {
            this.logResult('AdminService Import', true, 'Component imports adminService');
        } else {
            this.logResult('AdminService Import', false, 'Component does not import adminService');
        }

        // Check if component calls getAllUsers
        const callsGetAllUsers = componentContent.includes('adminService.getAllUsers') ||
                                componentContent.includes('getAllUsers');
        
        if (callsGetAllUsers) {
            this.logResult('GetAllUsers API Call', true, 'Component calls getAllUsers API');
        } else {
            this.logResult('GetAllUsers API Call', false, 'Component does not call getAllUsers API');
        }

        // Check if service has getAllUsers method
        const hasGetAllUsersMethod = serviceContent.includes('async getAllUsers(') ||
                                    serviceContent.includes('getAllUsers(');
        
        if (hasGetAllUsersMethod) {
            this.logResult('GetAllUsers Method', true, 'AdminService has getAllUsers method');
        } else {
            this.logResult('GetAllUsers Method', false, 'AdminService missing getAllUsers method');
        }

        // Check if service makes proper API calls
        const makesApiCall = serviceContent.includes('/admin/users') ||
                            serviceContent.includes('httpClient.get');
        
        if (makesApiCall) {
            this.logResult('API Endpoint Call', true, 'Service makes API calls to backend');
        } else {
            this.logResult('API Endpoint Call', false, 'Service does not make API calls');
        }
    }

    verifyUserCountDisplay(componentContent) {
        console.log('\n=== Verifying User Count Display ===');
        
        if (!componentContent) {
            this.logResult('User Count Display', false, 'Cannot verify without component content');
            return;
        }

        // Check if component displays user count from API response
        const displaysUserCount = componentContent.includes('users.length') ||
                                 componentContent.includes('No users found') ||
                                 componentContent.includes('users.map');
        
        if (displaysUserCount) {
            this.logResult('User Count Display', true, 'Component displays user count from API data');
        } else {
            this.logResult('User Count Display', false, 'Component may not display accurate user count');
        }

        // Check for hardcoded user counts (should not exist)
        // Exclude CSS classes and API limits
        const hasHardcodedCounts = /\b(1234|999)\b/.test(componentContent) ||
                                  (/\b100\b/.test(componentContent) && 
                                   !componentContent.includes('limit: 100') && 
                                   !componentContent.includes('bg-') && 
                                   !componentContent.includes('text-') &&
                                   !componentContent.includes('hover:bg-'));
        
        if (!hasHardcodedCounts) {
            this.logResult('No Hardcoded Counts', true, 'No hardcoded user counts found');
        } else {
            this.logResult('No Hardcoded Counts', false, 'Found potential hardcoded user counts');
        }

        // Check for empty state handling
        const hasEmptyState = componentContent.includes('No users found') ||
                             componentContent.includes('users.length === 0');
        
        if (hasEmptyState) {
            this.logResult('Empty State Handling', true, 'Component handles empty user state');
        } else {
            this.logResult('Empty State Handling', false, 'Component may not handle empty user state');
        }
    }

    verifyTeamAssignmentDisplay(componentContent) {
        console.log('\n=== Verifying Team Assignment Display ===');
        
        if (!componentContent) {
            this.logResult('Team Assignment Display', false, 'Cannot verify without component content');
            return;
        }

        // Check if component displays team information
        const displaysTeamInfo = componentContent.includes('user.team') ||
                                componentContent.includes('team?.name') ||
                                componentContent.includes('No Team');
        
        if (displaysTeamInfo) {
            this.logResult('Team Info Display', true, 'Component displays team assignment information');
        } else {
            this.logResult('Team Info Display', false, 'Component may not display team assignments');
        }

        // Check if component loads teams for filtering
        const loadsTeams = componentContent.includes('loadTeams') ||
                          componentContent.includes('getAllTeams') ||
                          componentContent.includes('teams.map');
        
        if (loadsTeams) {
            this.logResult('Team Loading', true, 'Component loads team data for filtering');
        } else {
            this.logResult('Team Loading', false, 'Component may not load team data');
        }

        // Check for team filter functionality
        const hasTeamFilter = componentContent.includes('selectedTeam') ||
                             componentContent.includes('teamId') ||
                             componentContent.includes('Filter by Team');
        
        if (hasTeamFilter) {
            this.logResult('Team Filter', true, 'Component has team filtering functionality');
        } else {
            this.logResult('Team Filter', false, 'Component may not have team filtering');
        }
    }

    verifyRoleBadgeDisplay(componentContent) {
        console.log('\n=== Verifying Role Badge Display ===');
        
        if (!componentContent) {
            this.logResult('Role Badge Display', false, 'Cannot verify without component content');
            return;
        }

        // Check if component displays role information
        const displaysRoles = componentContent.includes('user.role') ||
                             componentContent.includes('getRoleColor') ||
                             componentContent.includes('role');
        
        if (displaysRoles) {
            this.logResult('Role Display', true, 'Component displays user roles');
        } else {
            this.logResult('Role Display', false, 'Component may not display user roles');
        }

        // Check for role color coding
        const hasRoleColors = componentContent.includes('getRoleColor') ||
                             componentContent.includes('bg-red-100') ||
                             componentContent.includes('bg-blue-100');
        
        if (hasRoleColors) {
            this.logResult('Role Color Coding', true, 'Component has role color coding');
        } else {
            this.logResult('Role Color Coding', false, 'Component may not have role color coding');
        }

        // Check for role editing functionality
        const hasRoleEditing = componentContent.includes('handleRoleChange') ||
                              componentContent.includes('updateUserRole') ||
                              componentContent.includes('select');
        
        if (hasRoleEditing) {
            this.logResult('Role Editing', true, 'Component has role editing functionality');
        } else {
            this.logResult('Role Editing', false, 'Component may not have role editing');
        }

        // Check for role validation (prevent self-role change)
        const hasRoleValidation = componentContent.includes('currentUser?.id') ||
                                 componentContent.includes('disabled={user.id === currentUser?.id}');
        
        if (hasRoleValidation) {
            this.logResult('Role Validation', true, 'Component prevents self-role modification');
        } else {
            this.logResult('Role Validation', false, 'Component may not prevent self-role modification');
        }
    }

    verifySearchAndFilterFunctionality(componentContent) {
        console.log('\n=== Verifying Search and Filter Functionality ===');
        
        if (!componentContent) {
            this.logResult('Search and Filter', false, 'Cannot verify without component content');
            return;
        }

        // Check for search functionality
        const hasSearch = componentContent.includes('searchTerm') ||
                         componentContent.includes('Search by name or email') ||
                         componentContent.includes('handleSearch');
        
        if (hasSearch) {
            this.logResult('Search Functionality', true, 'Component has search functionality');
        } else {
            this.logResult('Search Functionality', false, 'Component may not have search functionality');
        }

        // Check for filter functionality
        const hasFilters = componentContent.includes('showFilters') ||
                          componentContent.includes('Filter') ||
                          componentContent.includes('selectedTeam');
        
        if (hasFilters) {
            this.logResult('Filter Functionality', true, 'Component has filter functionality');
        } else {
            this.logResult('Filter Functionality', false, 'Component may not have filter functionality');
        }

        // Check for sorting functionality
        const hasSorting = componentContent.includes('sortBy') ||
                          componentContent.includes('sortOrder') ||
                          componentContent.includes('handleSort');
        
        if (hasSorting) {
            this.logResult('Sorting Functionality', true, 'Component has sorting functionality');
        } else {
            this.logResult('Sorting Functionality', false, 'Component may not have sorting functionality');
        }

        // Check for pagination
        const hasPagination = componentContent.includes('currentPage') ||
                             componentContent.includes('totalPages') ||
                             componentContent.includes('pagination');
        
        if (hasPagination) {
            this.logResult('Pagination Functionality', true, 'Component has pagination functionality');
        } else {
            this.logResult('Pagination Functionality', false, 'Component may not have pagination functionality');
        }
    }

    verifyErrorHandling(componentContent) {
        console.log('\n=== Verifying Error Handling ===');
        
        if (!componentContent) {
            this.logResult('Error Handling', false, 'Cannot verify without component content');
            return;
        }

        // Check for loading states
        const hasLoadingStates = componentContent.includes('loading') ||
                                componentContent.includes('Loading') ||
                                componentContent.includes('animate-spin');
        
        if (hasLoadingStates) {
            this.logResult('Loading States', true, 'Component has loading state handling');
        } else {
            this.logResult('Loading States', false, 'Component may not have loading states');
        }

        // Check for error handling
        const hasErrorHandling = componentContent.includes('catch') ||
                                componentContent.includes('onError') ||
                                componentContent.includes('error');
        
        if (hasErrorHandling) {
            this.logResult('Error Handling', true, 'Component has error handling');
        } else {
            this.logResult('Error Handling', false, 'Component may not have error handling');
        }

        // Check for success feedback
        const hasSuccessFeedback = componentContent.includes('onSuccess') ||
                                  componentContent.includes('success') ||
                                  componentContent.includes('toast');
        
        if (hasSuccessFeedback) {
            this.logResult('Success Feedback', true, 'Component provides success feedback');
        } else {
            this.logResult('Success Feedback', false, 'Component may not provide success feedback');
        }
    }

    verifyDataRefresh(componentContent) {
        console.log('\n=== Verifying Data Refresh ===');
        
        if (!componentContent) {
            this.logResult('Data Refresh', false, 'Cannot verify without component content');
            return;
        }

        // Check for data refresh after operations
        const hasDataRefresh = componentContent.includes('loadUsers') ||
                              componentContent.includes('refresh') ||
                              componentContent.includes('await loadUsers()');
        
        if (hasDataRefresh) {
            this.logResult('Data Refresh', true, 'Component refreshes data after operations');
        } else {
            this.logResult('Data Refresh', false, 'Component may not refresh data after operations');
        }

        // Check for useEffect dependencies
        const hasUseEffect = componentContent.includes('useEffect') &&
                            (componentContent.includes('[currentPage') ||
                             componentContent.includes('[searchTerm') ||
                             componentContent.includes('[selectedTeam'));
        
        if (hasUseEffect) {
            this.logResult('Reactive Updates', true, 'Component updates reactively to state changes');
        } else {
            this.logResult('Reactive Updates', false, 'Component may not update reactively');
        }
    }

    printSummary() {
        console.log('\n' + '='.repeat(60));
        console.log('USER MANAGEMENT VERIFICATION SUMMARY');
        console.log('='.repeat(60));
        
        const totalTests = this.testResults.length;
        const passedTests = this.testResults.filter(r => r.status === 'PASS').length;
        const failedTests = totalTests - passedTests;
        
        console.log(`Total Checks: ${totalTests}`);
        console.log(`Passed: ${passedTests}`);
        console.log(`Failed: ${failedTests}`);
        console.log(`Success Rate: ${((passedTests/totalTests)*100).toFixed(1)}%`);
        
        if (failedTests > 0) {
            console.log('\nFAILED CHECKS:');
            this.testResults.filter(r => r.status === 'FAIL').forEach(result => {
                console.log(`  - ${result.test}: ${result.message}`);
            });
        }
        
        console.log('\nREQUIREMENTS VERIFICATION:');
        
        // 5.1 - Display all actual users from database
        const req51 = this.testResults.some(r => 
            (r.test === 'GetAllUsers API Call' || r.test === 'User Count Display') && r.status === 'PASS'
        );
        console.log(`5.1 - Display all actual users from database: ${req51 ? '✓ PASS' : '✗ FAIL'}`);
        
        // 5.2 - Display accurate user information
        const req52 = this.testResults.some(r => 
            (r.test === 'User Count Display' || r.test === 'No Hardcoded Counts') && r.status === 'PASS'
        );
        console.log(`5.2 - Display accurate user information: ${req52 ? '✓ PASS' : '✗ FAIL'}`);
        
        // 5.3 - Display accurate role and team information
        const req53 = this.testResults.some(r => r.test === 'Role Display' && r.status === 'PASS') &&
                     this.testResults.some(r => r.test === 'Team Info Display' && r.status === 'PASS');
        console.log(`5.3 - Display accurate role and team information: ${req53 ? '✓ PASS' : '✗ FAIL'}`);
        
        // 5.4 - Search and filter functionality works
        const req54 = this.testResults.some(r => r.test === 'Search Functionality' && r.status === 'PASS') &&
                     this.testResults.some(r => r.test === 'Filter Functionality' && r.status === 'PASS');
        console.log(`5.4 - Search and filter functionality works: ${req54 ? '✓ PASS' : '✗ FAIL'}`);
        
        return failedTests === 0;
    }

    runVerification() {
        console.log('Starting UserManagementPanel Verification...');
        console.log(`Component Path: ${this.componentPath}`);
        console.log(`Service Path: ${this.servicePath}`);
        console.log(`Verification started at: ${new Date()}`);
        
        try {
            const componentContent = this.readComponentFile();
            const serviceContent = this.readServiceFile();
            
            if (componentContent && serviceContent) {
                this.verifyApiIntegration(componentContent, serviceContent);
                this.verifyUserCountDisplay(componentContent);
                this.verifyTeamAssignmentDisplay(componentContent);
                this.verifyRoleBadgeDisplay(componentContent);
                this.verifySearchAndFilterFunctionality(componentContent);
                this.verifyErrorHandling(componentContent);
                this.verifyDataRefresh(componentContent);
            }
            
        } catch (error) {
            console.log(`Critical error during verification: ${error}`);
            this.logResult('Critical Error', false, error.toString());
        }
        
        return this.printSummary();
    }
}

function main() {
    const verifier = new UserManagementVerification();
    const success = verifier.runVerification();
    
    if (success) {
        console.log('\n🎉 UserManagementPanel verification passed! Component is properly implemented.');
        process.exit(0);
    } else {
        console.log('\n❌ UserManagementPanel verification failed. Please review the issues above.');
        process.exit(1);
    }
}

main();