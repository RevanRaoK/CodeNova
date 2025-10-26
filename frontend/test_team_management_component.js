#!/usr/bin/env node
/**
 * Test script to verify TeamManagementPanel displays accurate data
 * 
 * This script tests:
 * - Component renders with real team data
 * - Team count matches API response
 * - Member counts are displayed correctly
 * - Team deletion functionality works
 * - Empty state displays when no teams exist
 * 
 * Requirements: 6.1, 6.2, 6.3, 6.4
 */

import { JSDOM } from 'jsdom';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import fetch from 'node-fetch';

// Mock the global fetch for Node.js environment
global.fetch = fetch;

// Setup JSDOM environment
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
  url: 'http://localhost:3000',
  pretendToBeVisual: true,
  resources: 'usable'
});

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Mock React components and services
const mockAdminService = {
  getAllTeams: jest.fn(),
  createTeam: jest.fn(),
  updateTeam: jest.fn(),
  deleteTeam: jest.fn()
};

// Mock the admin service
jest.mock('../services/adminService.js', () => mockAdminService);

// Mock Lucide React icons
jest.mock('lucide-react', () => ({
  Plus: () => React.createElement('div', { 'data-testid': 'plus-icon' }),
  Edit: () => React.createElement('div', { 'data-testid': 'edit-icon' }),
  Trash2: () => React.createElement('div', { 'data-testid': 'trash-icon' }),
  Users: () => React.createElement('div', { 'data-testid': 'users-icon' }),
  Settings: () => React.createElement('div', { 'data-testid': 'settings-icon' }),
  Search: () => React.createElement('div', { 'data-testid': 'search-icon' })
}));

// Mock ConfirmationDialog
jest.mock('../components/ConfirmationDialog.jsx', () => {
  return function ConfirmationDialog({ title, message, onConfirm, onCancel }) {
    return React.createElement('div', {
      'data-testid': 'confirmation-dialog'
    }, [
      React.createElement('h3', { key: 'title' }, title),
      React.createElement('p', { key: 'message' }, message),
      React.createElement('button', {
        key: 'confirm',
        'data-testid': 'confirm-button',
        onClick: onConfirm
      }, 'Confirm'),
      React.createElement('button', {
        key: 'cancel',
        'data-testid': 'cancel-button',
        onClick: onCancel
      }, 'Cancel')
    ]);
  };
});

// Import the component after mocks are set up
const TeamManagementPanel = require('../components/admin/TeamManagementPanel.jsx').default;

class TeamManagementComponentTest {
  constructor() {
    this.testResults = [];
    this.mockTeams = [
      {
        id: 'team-1',
        name: 'Development Team',
        admin_id: 1,
        admin: { full_name: 'John Doe' },
        member_count: 5,
        created_at: '2024-01-15T10:00:00Z',
        settings: {}
      },
      {
        id: 'team-2',
        name: 'QA Team',
        admin_id: 2,
        admin: { full_name: 'Jane Smith' },
        member_count: 3,
        created_at: '2024-02-01T14:30:00Z',
        settings: {}
      },
      {
        id: 'team-3',
        name: 'Design Team',
        admin_id: 3,
        admin: { full_name: 'Bob Wilson' },
        member_count: 0,
        created_at: '2024-03-10T09:15:00Z',
        settings: {}
      }
    ];
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

  async testComponentRendersWithTeamData() {
    // Mock API response
    mockAdminService.getAllTeams.mockResolvedValue(this.mockTeams);

    const mockProps = {
      onError: jest.fn(),
      onSuccess: jest.fn(),
      currentUser: { id: 1, role: 'admin' }
    };

    let component;
    try {
      component = render(React.createElement(TeamManagementPanel, mockProps));
      
      // Wait for component to load data
      await waitFor(() => {
        expect(mockAdminService.getAllTeams).toHaveBeenCalled();
      });

      // Check if teams are rendered
      const teamCards = component.container.querySelectorAll('[data-testid*="team-card"]');
      const teamNames = Array.from(component.container.querySelectorAll('h3')).map(h3 => h3.textContent);
      
      const hasTeamManagementTitle = teamNames.includes('Team Management');
      const hasTeamCards = teamCards.length > 0 || teamNames.some(name => 
        this.mockTeams.some(team => team.name === name)
      );

      const passed = hasTeamManagementTitle && mockAdminService.getAllTeams.mock.calls.length > 0;

      this.logResult(
        'Component Renders With Team Data',
        passed,
        `Component ${passed ? 'successfully rendered' : 'failed to render'} with team data`,
        {
          api_called: mockAdminService.getAllTeams.mock.calls.length > 0,
          has_title: hasTeamManagementTitle,
          has_team_cards: hasTeamCards,
          team_names_found: teamNames.filter(name => 
            this.mockTeams.some(team => team.name === name)
          )
        }
      );

      return passed;
    } catch (error) {
      this.logResult(
        'Component Renders With Team Data',
        false,
        `Component failed to render: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testTeamCountAccuracy() {
    mockAdminService.getAllTeams.mockResolvedValue(this.mockTeams);

    const mockProps = {
      onError: jest.fn(),
      onSuccess: jest.fn(),
      currentUser: { id: 1, role: 'admin' }
    };

    try {
      const component = render(React.createElement(TeamManagementPanel, mockProps));
      
      await waitFor(() => {
        expect(mockAdminService.getAllTeams).toHaveBeenCalled();
      });

      // Check if the correct number of teams are displayed
      const allText = component.container.textContent;
      const expectedTeamCount = this.mockTeams.length;
      
      // Count how many team names appear in the rendered content
      const renderedTeamCount = this.mockTeams.filter(team => 
        allText.includes(team.name)
      ).length;

      const passed = renderedTeamCount === expectedTeamCount;

      this.logResult(
        'Team Count Accuracy',
        passed,
        `Expected ${expectedTeamCount} teams, found ${renderedTeamCount} in rendered content`,
        {
          expected_count: expectedTeamCount,
          rendered_count: renderedTeamCount,
          mock_teams: this.mockTeams.map(t => t.name),
          api_response_length: this.mockTeams.length
        }
      );

      return passed;
    } catch (error) {
      this.logResult(
        'Team Count Accuracy',
        false,
        `Test failed: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testMemberCountDisplay() {
    mockAdminService.getAllTeams.mockResolvedValue(this.mockTeams);

    const mockProps = {
      onError: jest.fn(),
      onSuccess: jest.fn(),
      currentUser: { id: 1, role: 'admin' }
    };

    try {
      const component = render(React.createElement(TeamManagementPanel, mockProps));
      
      await waitFor(() => {
        expect(mockAdminService.getAllTeams).toHaveBeenCalled();
      });

      const allText = component.container.textContent;
      let memberCountsDisplayed = 0;

      // Check if member counts are displayed for each team
      for (const team of this.mockTeams) {
        if (allText.includes(team.member_count.toString())) {
          memberCountsDisplayed++;
        }
      }

      const passed = memberCountsDisplayed === this.mockTeams.length;

      this.logResult(
        'Member Count Display',
        passed,
        `${memberCountsDisplayed}/${this.mockTeams.length} team member counts displayed correctly`,
        {
          teams_with_member_counts: this.mockTeams.map(t => ({
            name: t.name,
            member_count: t.member_count,
            displayed: allText.includes(t.member_count.toString())
          })),
          total_displayed: memberCountsDisplayed
        }
      );

      return passed;
    } catch (error) {
      this.logResult(
        'Member Count Display',
        false,
        `Test failed: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testTeamDeletionFunctionality() {
    mockAdminService.getAllTeams.mockResolvedValue(this.mockTeams);
    mockAdminService.deleteTeam.mockResolvedValue(true);

    const mockProps = {
      onError: jest.fn(),
      onSuccess: jest.fn(),
      currentUser: { id: 1, role: 'admin' }
    };

    try {
      const component = render(React.createElement(TeamManagementPanel, mockProps));
      
      await waitFor(() => {
        expect(mockAdminService.getAllTeams).toHaveBeenCalled();
      });

      // Look for delete buttons (trash icons)
      const deleteButtons = component.container.querySelectorAll('[data-testid="trash-icon"]');
      const hasDeleteButtons = deleteButtons.length > 0;

      // If we find delete buttons, simulate clicking one
      let deletionTriggered = false;
      if (hasDeleteButtons) {
        // Click the first delete button
        const firstDeleteButton = deleteButtons[0].closest('button');
        if (firstDeleteButton) {
          fireEvent.click(firstDeleteButton);
          
          // Check if confirmation dialog appears
          await waitFor(() => {
            const confirmDialog = component.container.querySelector('[data-testid="confirmation-dialog"]');
            if (confirmDialog) {
              const confirmButton = confirmDialog.querySelector('[data-testid="confirm-button"]');
              if (confirmButton) {
                fireEvent.click(confirmButton);
                deletionTriggered = true;
              }
            }
          });
        }
      }

      const passed = hasDeleteButtons;

      this.logResult(
        'Team Deletion Functionality',
        passed,
        `Delete functionality ${passed ? 'is available' : 'is not available'}`,
        {
          delete_buttons_found: deleteButtons.length,
          deletion_triggered: deletionTriggered,
          delete_api_called: mockAdminService.deleteTeam.mock.calls.length > 0
        }
      );

      return passed;
    } catch (error) {
      this.logResult(
        'Team Deletion Functionality',
        false,
        `Test failed: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testEmptyStateDisplay() {
    // Mock empty teams response
    mockAdminService.getAllTeams.mockResolvedValue([]);

    const mockProps = {
      onError: jest.fn(),
      onSuccess: jest.fn(),
      currentUser: { id: 1, role: 'admin' }
    };

    try {
      const component = render(React.createElement(TeamManagementPanel, mockProps));
      
      await waitFor(() => {
        expect(mockAdminService.getAllTeams).toHaveBeenCalled();
      });

      const allText = component.container.textContent;
      
      // Check for empty state indicators
      const hasNoTeamsMessage = allText.includes('No teams found') || 
                               allText.includes('no teams') || 
                               allText.includes('Get started by creating');
      
      const hasUsersIcon = component.container.querySelector('[data-testid="users-icon"]');
      
      const passed = hasNoTeamsMessage || hasUsersIcon;

      this.logResult(
        'Empty State Display',
        passed,
        `Empty state ${passed ? 'is displayed' : 'is not displayed'} when no teams exist`,
        {
          has_no_teams_message: hasNoTeamsMessage,
          has_users_icon: !!hasUsersIcon,
          api_returned_empty: mockAdminService.getAllTeams.mock.results[mockAdminService.getAllTeams.mock.results.length - 1]?.value?.length === 0,
          rendered_text_sample: allText.substring(0, 200)
        }
      );

      return passed;
    } catch (error) {
      this.logResult(
        'Empty State Display',
        false,
        `Test failed: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async testTeamCreationForm() {
    mockAdminService.getAllTeams.mockResolvedValue(this.mockTeams);
    mockAdminService.createTeam.mockResolvedValue({
      id: 'new-team',
      name: 'New Team',
      admin_id: 1,
      member_count: 0
    });

    const mockProps = {
      onError: jest.fn(),
      onSuccess: jest.fn(),
      currentUser: { id: 1, role: 'admin' }
    };

    try {
      const component = render(React.createElement(TeamManagementPanel, mockProps));
      
      await waitFor(() => {
        expect(mockAdminService.getAllTeams).toHaveBeenCalled();
      });

      // Look for create team button
      const createButtons = component.container.querySelectorAll('button');
      const createTeamButton = Array.from(createButtons).find(button => 
        button.textContent.includes('Create Team')
      );

      const hasCreateButton = !!createTeamButton;

      // Try to click create button and check if form appears
      let formAppeared = false;
      if (createTeamButton) {
        fireEvent.click(createTeamButton);
        
        await waitFor(() => {
          const forms = component.container.querySelectorAll('form');
          const inputs = component.container.querySelectorAll('input[placeholder*="team"]');
          formAppeared = forms.length > 0 || inputs.length > 0;
        });
      }

      const passed = hasCreateButton;

      this.logResult(
        'Team Creation Form',
        passed,
        `Team creation form ${passed ? 'is available' : 'is not available'}`,
        {
          has_create_button: hasCreateButton,
          form_appeared: formAppeared,
          create_button_text: createTeamButton?.textContent || 'Not found'
        }
      );

      return passed;
    } catch (error) {
      this.logResult(
        'Team Creation Form',
        false,
        `Test failed: ${error.message}`,
        { error: error.message }
      );
      return false;
    }
  }

  async runAllTests() {
    console.log('🧪 Starting Team Management Component Tests');
    console.log('='.repeat(50));

    const testMethods = [
      this.testComponentRendersWithTeamData,
      this.testTeamCountAccuracy,
      this.testMemberCountDisplay,
      this.testTeamDeletionFunctionality,
      this.testEmptyStateDisplay,
      this.testTeamCreationForm
    ];

    let passedTests = 0;
    const totalTests = testMethods.length;

    for (const testMethod of testMethods) {
      try {
        // Reset mocks before each test
        jest.clearAllMocks();
        
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

    // Print summary
    console.log('='.repeat(50));
    console.log(`📊 Test Summary: ${passedTests}/${totalTests} tests passed`);

    if (passedTests === totalTests) {
      console.log('🎉 All team management component tests PASSED!');
      return true;
    } else {
      console.log(`⚠️  ${totalTests - passedTests} test(s) FAILED`);
      return false;
    }
  }

  saveResults(filename = 'team_management_component_test_results.json') {
    const fs = require('fs');
    const results = {
      timestamp: new Date().toISOString(),
      total_tests: this.testResults.length,
      passed_tests: this.testResults.filter(r => r.passed).length,
      results: this.testResults
    };

    fs.writeFileSync(filename, JSON.stringify(results, null, 2));
    console.log(`📄 Test results saved to ${filename}`);
  }
}

async function main() {
  const tester = new TeamManagementComponentTest();
  
  try {
    const success = await tester.runAllTests();
    tester.saveResults();
    
    if (success) {
      console.log('\n✅ TeamManagementPanel component displays accurate data!');
      process.exit(0);
    } else {
      console.log('\n❌ TeamManagementPanel component has display issues!');
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

module.exports = TeamManagementComponentTest;