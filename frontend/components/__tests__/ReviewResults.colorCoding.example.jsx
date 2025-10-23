/**
 * Example usage of ReviewResults component with color coding
 * 
 * This file demonstrates how to use the ReviewResults component
 * with different severity levels to see the color coding in action.
 */

import React from 'react'
import { ReviewResults } from '../ReviewResults'

// Example issues with different severity levels
const exampleIssues = [
  {
    id: 'issue-1',
    line: 15,
    column: 8,
    severity: 'critical',
    message: 'SQL injection vulnerability detected in user input handling',
    suggestion: 'Use parameterized queries or prepared statements to prevent SQL injection',
    codeExample: `// Bad
const query = \`SELECT * FROM users WHERE id = \${userId}\`;

// Good
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);`,
    category: 'security',
    rule: 'no-sql-injection'
  },
  {
    id: 'issue-2',
    line: 42,
    column: 12,
    severity: 'high',
    message: 'Memory leak detected: Event listener not removed on component unmount',
    suggestion: 'Add cleanup function in useEffect to remove event listeners',
    codeExample: `useEffect(() => {
  const handleResize = () => { /* ... */ };
  window.addEventListener('resize', handleResize);
  
  // Cleanup
  return () => {
    window.removeEventListener('resize', handleResize);
  };
}, []);`,
    category: 'performance',
    rule: 'react-hooks/exhaustive-deps'
  },
  {
    id: 'issue-3',
    line: 78,
    column: 5,
    severity: 'warning',
    message: 'Unused variable "userData" declared but never used',
    suggestion: 'Remove the unused variable or use it in your code',
    category: 'code-quality',
    rule: 'no-unused-vars'
  },
  {
    id: 'issue-4',
    line: 103,
    column: 15,
    severity: 'low',
    message: 'Variable name "x" is not descriptive',
    suggestion: 'Use a more descriptive name like "userCount" or "totalItems"',
    codeExample: `// Bad
const x = users.length;

// Good
const userCount = users.length;`,
    category: 'naming',
    rule: 'naming-convention'
  },
  {
    id: 'issue-5',
    line: 125,
    column: 1,
    severity: 'info',
    message: 'Function lacks JSDoc documentation',
    suggestion: 'Add JSDoc comments to document function parameters and return value',
    codeExample: `/**
 * Calculates the total price including tax
 * @param {number} price - The base price
 * @param {number} taxRate - The tax rate (e.g., 0.08 for 8%)
 * @returns {number} The total price with tax
 */
function calculateTotal(price, taxRate) {
  return price * (1 + taxRate);
}`,
    category: 'documentation',
    rule: 'jsdoc-required'
  },
  {
    id: 'issue-6',
    line: 156,
    column: 20,
    severity: 'suggestion',
    message: 'Consider using async/await instead of promise chains',
    suggestion: 'Modern async/await syntax is more readable and easier to maintain',
    codeExample: `// Using promises
fetchUser(userId)
  .then(user => fetchPosts(user.id))
  .then(posts => console.log(posts))
  .catch(error => console.error(error));

// Using async/await
try {
  const user = await fetchUser(userId);
  const posts = await fetchPosts(user.id);
  console.log(posts);
} catch (error) {
  console.error(error);
}`,
    category: 'suggestion',
    rule: 'prefer-async-await'
  },
  {
    id: 'issue-7',
    line: 189,
    column: 10,
    severity: 'error', // Legacy severity - should display as red like critical
    message: 'Undefined variable "config" referenced',
    suggestion: 'Declare the variable before using it or import it from the config module',
    category: 'error',
    rule: 'no-undef'
  }
]

/**
 * Example component showing ReviewResults with color coding
 */
export function ReviewResultsColorCodingExample() {
  const handleIssueClick = (issue) => {
    console.log('Issue clicked:', issue)
    // Navigate to the issue in the code editor
  }

  const handleFeedbackSubmitted = (feedback) => {
    console.log('Feedback submitted:', feedback)
    // Handle feedback submission
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            ReviewResults Color Coding Example
          </h1>
          <p className="text-gray-600">
            This example demonstrates the color coding feature for different issue severity levels.
            Each issue is displayed with a distinct color to help you quickly identify priority.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <ReviewResults
            issues={exampleIssues}
            onIssueClick={handleIssueClick}
            enableFeedback={true}
            onFeedbackSubmitted={handleFeedbackSubmitted}
            analysisMetrics={{
              linesOfCode: 250,
              complexity: 12,
              maintainabilityIndex: 78
            }}
          />
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-3">
            Color Coding Guide
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-red-100 border-2 border-red-300 rounded"></div>
              <div>
                <span className="font-medium text-gray-900">Critical (Red)</span>
                <p className="text-gray-600">Security vulnerabilities, critical bugs</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-orange-100 border-2 border-orange-300 rounded"></div>
              <div>
                <span className="font-medium text-gray-900">High (Orange)</span>
                <p className="text-gray-600">Memory leaks, performance issues</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-yellow-100 border-2 border-yellow-300 rounded"></div>
              <div>
                <span className="font-medium text-gray-900">Warning (Yellow)</span>
                <p className="text-gray-600">Unused variables, deprecated APIs</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-100 border-2 border-blue-300 rounded"></div>
              <div>
                <span className="font-medium text-gray-900">Low (Blue)</span>
                <p className="text-gray-600">Naming conventions, minor improvements</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-gray-100 border-2 border-gray-300 rounded"></div>
              <div>
                <span className="font-medium text-gray-900">Info (Gray)</span>
                <p className="text-gray-600">Documentation, informational messages</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-green-100 border-2 border-green-300 rounded"></div>
              <div>
                <span className="font-medium text-gray-900">Suggestion (Green)</span>
                <p className="text-gray-600">Helpful suggestions, best practices</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-green-900 mb-2">
            ✅ Features Implemented
          </h2>
          <ul className="space-y-2 text-sm text-green-800">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Color-coded issue containers with left border accent</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Distinct icons for each severity level</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Green background for suggestion sections</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Case-insensitive severity handling</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>WCAG AA compliant color contrast</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              <span>Backward compatibility with legacy "error" severity</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default ReviewResultsColorCodingExample
