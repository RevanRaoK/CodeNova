#!/usr/bin/env node

/**
 * Test Runner Script
 * Provides convenient commands for running different test suites
 */

const { spawn } = require('child_process');
const path = require('path');

const commands = {
  all: ['vitest', '--run'],
  unit: ['vitest', '--run', 'components/__tests__/'],
  integration: ['vitest', '--run', 'services/__tests__/', 'contexts/__tests__/'],
  e2e: ['vitest', '--run', '__tests__/e2e/'],
  watch: ['vitest', '--watch'],
  coverage: ['vitest', '--run', '--coverage'],
  ui: ['vitest', '--ui'],
  notification: ['vitest', '--run', 'NotificationSystem.test.jsx'],
  monaco: ['vitest', '--run', 'MonacoEditor'],
  auth: ['vitest', '--run', 'AuthContext.test.jsx'],
  api: ['vitest', '--run', 'apiService.integration.test.js'],
  workflow: ['vitest', '--run', 'codeReviewWorkflow.test.jsx']
};

function runCommand(cmd, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, {
      stdio: 'inherit',
      cwd: process.cwd(),
      shell: true
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });

    child.on('error', (error) => {
      reject(error);
    });
  });
}

function showHelp() {
  console.log(`
CodeReview AI Test Runner

Usage: node scripts/test-runner.js [command]

Available commands:
  all         - Run all tests
  unit        - Run unit tests only
  integration - Run integration tests only
  e2e         - Run end-to-end tests only
  watch       - Run tests in watch mode
  coverage    - Run tests with coverage report
  ui          - Open Vitest UI
  notification- Run notification system tests
  monaco      - Run Monaco Editor tests
  auth        - Run authentication tests
  api         - Run API service tests
  workflow    - Run workflow tests
  help        - Show this help message

Examples:
  node scripts/test-runner.js all
  node scripts/test-runner.js unit
  node scripts/test-runner.js watch
  node scripts/test-runner.js coverage
`);
}

async function main() {
  const command = process.argv[2] || 'help';

  if (command === 'help' || !commands[command]) {
    showHelp();
    return;
  }

  console.log(`Running ${command} tests...`);
  
  try {
    const [cmd, ...args] = commands[command];
    await runCommand(cmd, args);
    console.log(`✅ ${command} tests completed successfully`);
  } catch (error) {
    console.error(`❌ ${command} tests failed:`, error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { runCommand, commands };