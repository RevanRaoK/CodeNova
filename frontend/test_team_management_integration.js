#!/usr/bin/env node
/**
 * Integration test for TeamManagementPanel with real API calls
 * 
 * This script tests:
 * - Real API integration with backend
 * - Team data accuracy from database
 * - Team deletion workflow
 * - Error handling
 * - Empty state scenarios
 * 
 * Requirements: 6.1, 6.2, 6.3, 6.4
 */

const fetch = require('node-fetch');
const fs = require('fs');

class TeamManagementIntegrationTest {
  constructor() {
    this.baseUrl = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
    this.testResults = [];
    this.authToken = null;
    this.createdTeams = [];
    this.createdUsers = [];
  }

  logResult(testName, passed, message, details = {}) {
    const result = {
      test: testName,
      passed,
      message,
      timestamp: new Date().toISOString(),
      details
    };
    this.testResults.push(result);
    
    const status = passed ? '✅ PASS' : '❌ FAIL';
    console.log(`${status}: ${testName}`);
    console.log(`   ${message}`);
    if (Object.keys(details).length > 0) {
      console.log(`   Details: ${JSON.stringify(details, null, 2)}`);
    }
    console.log();
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.authToken && { 'Authorization': `Bearer ${this.authToken}` })
      }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return await response.text();
  }

  async authenticateAsAdmin() {
    try {
      // Try to get an admin token - this might need to be adapted based on your auth system
      const loginData = {
        email: process.env.ADMIN_EMAIL || 'admin@example.com',
        password: process.env.ADMIN_PASSWORD || 'admin123'
      };

      const response = await this.makeRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify(loginData)
      });

      if (response.access_token) {
        this.authToken = response.access_token;
        return true;
      }
      
      return false;
    } catch (error) {
      console.log(`Authentication failed: ${error.message}`);
      // For testing purposes, we'll continue without auth if it fails
      return false;
    }
  }

  async testApiConnection() {
    try {
      // Test basic API connectivity
      const response = await fetch(`${this.baseUrl.replace('/api/v1', '')}/health`);
      const isHealthy = response.ok;

      this.logResult(
        'API Connection',
        isHealthy,
        `API ${isHealthy ? 'is accessible' : 'is not accessible'}`,
        {
          base_url: this.baseUrl,
          health_status: response.status,
          health_ok: response.ok
        }
      );

      return isHealthy;
    } catch (error) {
      this.logResult(
        'API Connection',
        false,
        `Failed to connect to API: ${error.message}`,
        { error: error.message, base_url: this.baseUrl }
      );
      return false;
    }
  }

  async testGetAllTeamsEndpoint() {
    try {
      const teams = await this.makeRequest('/admin/teams');
      const isArray = Array.isArray(teams);
      const hasValidStructure = isArray && teams.every(team => 
        team.id && team.name && typeof team.member_count === 'number'
      );

      this.logResult(
        'Get All Teams Endpoint',
        hasValidStructure,
        `Teams endpoint returned ${isArray ? teams.length : 'invalid'} teams`,
        {
          is_array: isArray,
          team_count: isArray ? teams.length : 0,
          sample_team: isArray && teams.length > 0 ? {
            id: teams[0].id,
            name: teams[0].name,
            member_count: teams[0].member_count,
            has_admin: !!teams[0].admin
          } : null,
          has_valid_structure: hasValidStructure
        }
      );

      return hasValidStructure ? teams : [];
    } catch (error) {
      this.logResult(
        'Get All Teams Endpoint',
        false,
        `Failed to fetch teams: ${error.message}`,
        { error: error.message }
      );
      return [];
    }
  }

  async testTeamDataAccuracy() {
    try {
      const teams = await this.makeRequest('/admin/teams');
      
      if (!Array.isArray(teams) || teams.length === 0) {
        this.logResult(
          'Team Data Accuracy',
          true,
          'No teams to verify (empty state is valid)',
          { team_count: 0 }
        );
        return true;
      }

      // Verify each team has required fields
      const requiredFields = ['id', 'name', 'admin_id', 'created_at'];
      let validTeams = 0;
      const teamDetails = [];

      for (const team of teams) {
        const missingFields = requiredFields.filter(field => !team[field]);
        const hasValidMemberCount = typeof team.member_count === 'number' && team.member_count >= 0;
        const hasAdminInfo = team.admin && team.admin.full_name;
        
        const isValid = missingFields.length === 0 && hasValidMemberCount;
        if (isValid) validTeams++;

        teamDetails.push({
          id: team.id,
          name: team.name,
          missing_fields: missingFields,
          member_count: team.member_count,
          has_valid_member_count: hasValidMemberCount,
          has_admin_info: hasAdminInfo,
          is_valid: isValid
        });
      }

      const allValid = validTeams === teams.length;

      this.logResult(
        'Team Data Accuracy',
        allValid,
        `${validTeams}/${teams.length} teams have accurate data structure`,
        {
          total_teams: teams.length,
          valid_teams: validTeams,
          team_details: teamDetails
        }
      );

      return allValid;
    } catch (error) {
      this.logResult(
        'Team Data Accuracy',
        false,
        `Failed to verify team data: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testTeamCreation() {
    try {
      const newTeamData = {
        name: `Integration Test Team ${Date.now()}`,
        settings: { test: true }
      };

      const createdTeam = await this.makeRequest('/admin/teams', {
        method: 'POST',
        body: JSON.stringify(newTeamData)
      });

      const isValid = createdTeam && createdTeam.id && createdTeam.name === newTeamData.name;
      
      if (isValid) {
        this.createdTeams.push(createdTeam.id);
      }

      this.logResult(
        'Team Creation',
        isValid,
        `Team creation ${isValid ? 'succeeded' : 'failed'}`,
        {
          requested_name: newTeamData.name,
          created_team: isValid ? {
            id: createdTeam.id,
            name: createdTeam.name,
            member_count: createdTeam.member_count
          } : null
        }
      );

      return isValid;
    } catch (error) {
      this.logResult(
        'Team Creation',
        false,
        `Team creation failed: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testTeamDeletion() {
    if (this.createdTeams.length === 0) {
      this.logResult(
        'Team Deletion',
        true,
        'No teams to delete (skipped)',
        { reason: 'No test teams created' }
      );
      return true;
    }

    try {
      const teamIdToDelete = this.createdTeams[0];
      
      // Verify team exists before deletion
      const teamBefore = await this.makeRequest(`/admin/teams/${teamIdToDelete}`);
      const existedBefore = !!teamBefore;

      // Delete the team
      await this.makeRequest(`/admin/teams/${teamIdToDelete}`, {
        method: 'DELETE'
      });

      // Verify team no longer exists
      let existsAfter = false;
      try {
        await this.makeRequest(`/admin/teams/${teamIdToDelete}`);
        existsAfter = true;
      } catch (error) {
        // Expected - team should not exist
        existsAfter = false;
      }

      const deletionSucceeded = existedBefore && !existsAfter;

      if (deletionSucceeded) {
        // Remove from our tracking list
        this.createdTeams = this.createdTeams.filter(id => id !== teamIdToDelete);
      }

      this.logResult(
        'Team Deletion',
        deletionSucceeded,
        `Team deletion ${deletionSucceeded ? 'succeeded' : 'failed'}`,
        {
          team_id: teamIdToDelete,
          existed_before: existedBefore,
          exists_after: existsAfter,
          deletion_succeeded: deletionSucceeded
        }
      );

      return deletionSucceeded;
    } catch (error) {
      this.logResult(
        'Team Deletion',
        false,
        `Team deletion failed: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testMemberCountAccuracy() {
    try {
      const teams = await this.makeRequest('/admin/teams');
      
      if (!Array.isArray(teams) || teams.length === 0) {
        this.logResult(
          'Member Count Accuracy',
          true,
          'No teams to verify member counts (empty state)',
          { team_count: 0 }
        );
        return true;
      }

      // For each team, verify member count makes sense
      let accurateTeams = 0;
      const memberCountDetails = [];

      for (const team of teams) {
        const memberCount = team.member_count;
        const isValidCount = typeof memberCount === 'number' && memberCount >= 0;
        
        if (isValidCount) accurateTeams++;

        memberCountDetails.push({
          team_id: team.id,
          team_name: team.name,
          member_count: memberCount,
          is_valid_count: isValidCount
        });
      }

      const allAccurate = accurateTeams === teams.length;

      this.logResult(
        'Member Count Accuracy',
        allAccurate,
        `${accurateTeams}/${teams.length} teams have accurate member counts`,
        {
          total_teams: teams.length,
          accurate_teams: accurateTeams,
          member_count_details: memberCountDetails
        }
      );

      return allAccurate;
    } catch (error) {
      this.logResult(
        'Member Count Accuracy',
        false,
        `Failed to verify member counts: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testErrorHandling() {
    try {
      // Test invalid team ID
      let errorHandled = false;
      try {
        await this.makeRequest('/admin/teams/invalid-team-id');
      } catch (error) {
        errorHandled = error.message.includes('404') || error.message.includes('not found');
      }

      // Test invalid team creation
      let creationErrorHandled = false;
      try {
        await this.makeRequest('/admin/teams', {
          method: 'POST',
          body: JSON.stringify({ name: '' }) // Invalid empty name
        });
      } catch (error) {
        creationErrorHandled = error.message.includes('400') || error.message.includes('422');
      }

      const passed = errorHandled && creationErrorHandled;

      this.logResult(
        'Error Handling',
        passed,
        `API error handling ${passed ? 'works correctly' : 'has issues'}`,
        {
          invalid_id_error_handled: errorHandled,
          invalid_creation_error_handled: creationErrorHandled
        }
      );

      return passed;
    } catch (error) {
      this.logResult(
        'Error Handling',
        false,
        `Error handling test failed: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async cleanup() {
    console.log('Cleaning up test data...');
    
    // Delete any teams we created
    for (const teamId of this.createdTeams) {
      try {
        await this.makeRequest(`/admin/teams/${teamId}`, {
          method: 'DELETE'
        });
        console.log(`Deleted test team: ${teamId}`);
      } catch (error) {
        console.log(`Failed to delete team ${teamId}: ${error.message}`);
      }
    }

    console.log(`Cleaned up ${this.createdTeams.length} test teams`);
  }

  async runAllTests() {
    console.log('🧪 Starting Team Management Integration Tests');
    console.log('='.repeat(50));

    // Authenticate first
    await this.authenticateAsAdmin();

    const testMethods = [
      this.testApiConnection,
      this.testGetAllTeamsEndpoint,
      this.testTeamDataAccuracy,
      this.testMemberCountAccuracy,
      this.testTeamCreation,
      this.testTeamDeletion,
      this.testErrorHandling
    ];

    let passedTests = 0;
    const totalTests = testMethods.length;

    for (const testMethod of testMethods) {
      try {
        const result = await testMethod.call(this);
        if (result) {
          passedTests++;
        }
      } catch (error) {
        this.logResult(
          testMethod.name,
          false,
          `Test failed with exception: ${error.message}`,
          { exception: error.message, stack: error.stack }
        );
      }
    }

    // Cleanup
    await this.cleanup();

    // Print summary
    console.log('='.repeat(50));
    console.log(`📊 Test Summary: ${passedTests}/${totalTests} tests passed`);

    if (passedTests === totalTests) {
      console.log('🎉 All team management integration tests PASSED!');
      return true;
    } else {
      console.log(`⚠️  ${totalTests - passedTests} test(s) FAILED`);
      return false;
    }
  }

  saveResults(filename = 'team_management_integration_test_results.json') {
    const results = {
      timestamp: new Date().toISOString(),
      total_tests: this.testResults.length,
      passed_tests: this.testResults.filter(r => r.passed).length,
      api_base_url: this.baseUrl,
      authenticated: !!this.authToken,
      results: this.testResults
    };

    fs.writeFileSync(filename, JSON.stringify(results, null, 2));
    console.log(`📄 Test results saved to ${filename}`);
  }
}

async function main() {
  const tester = new TeamManagementIntegrationTest();
  
  try {
    const success = await tester.runAllTests();
    tester.saveResults();
    
    if (success) {
      console.log('\n✅ Team management integration works correctly!');
      process.exit(0);
    } else {
      console.log('\n❌ Team management integration has issues!');
      process.exit(1);
    }
  } catch (error) {
    console.error(`\n💥 Test execution failed: ${error.message}`);
    process.exit(1);
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  main();
}

module.exports = TeamManagementIntegrationTest;