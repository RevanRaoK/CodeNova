#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

const testType = process.argv[2] || 'all';

const testCommands = {
  unit: ['vitest', 'run', 'contexts/__tests__/', 'components/__tests__/'],
  integration: ['vitest', 'run', 'services/__tests__/'],
  e2e: ['vitest', 'run', '__tests__/e2e/'],
  coverage: ['vitest', 'run', '--coverage'],
  watch: ['vitest', '--watch'],
  all: ['vitest', 'run'],
  auth: ['vitest', 'run', 'contexts/__tests__/AuthContext.test.jsx', 'services/__tests__/apiService.integration.test.js']
};

const command = testCommands[testType];

if (!command) {
  console.error(`Unknown test type: ${testType}`);
  console.error(`Available types: ${Object.keys(testCommands).join(', ')}`);
  process.exit(1);
}

console.log(`Running ${testType} tests...`);
console.log(`Command: ${command.join(' ')}`);

const child = spawn(command[0], command.slice(1), {
  stdio: 'inherit',
  cwd: process.cwd(),
  shell: process.platform === 'win32'
});

child.on('close', (code) => {
  process.exit(code);
});

child.on('error', (error) => {
  console.error('Failed to start test process:', error);
  process.exit(1);
});