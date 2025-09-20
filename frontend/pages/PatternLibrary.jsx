import React, { useState } from 'react'
import { PatternVisualizer } from '../components/PatternVisualizer'
import { SearchIcon, FilterIcon } from 'lucide-react'

export function PatternLibrary() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedSeverity, setSelectedSeverity] = useState('all')
  const [selectedCategory, setSelectedCategory] = useState('all')

  const mockPatterns = [
    {
      id: '1',
      name: 'Unchecked Null References',
      description:
        'Accessing properties or methods without checking if the object is null can lead to runtime exceptions.',
      frequency: 0.78,
      severity: 'high',
      examples: [
        'const name = user.profile.name; // No null check on user or profile',
        'if (user && user.profile && user.profile.name) { /* safer approach */ }',
      ],
    },
    {
      id: '2',
      name: 'Memory Leaks in Closures',
      description:
        'Functions that maintain references to large objects can prevent garbage collection.',
      frequency: 0.42,
      severity: 'medium',
      examples: [
        'function createLeak() { const largeData = [/* lots of data */]; return () => console.log(largeData.length); }',
        'function noLeak() { const size = [/* lots of data */].length; return () => console.log(size); }',
      ],
    },
    {
      id: '3',
      name: 'Inefficient Loop Patterns',
      description:
        'Certain loop patterns can cause performance issues, especially with large datasets.',
      frequency: 0.65,
      severity: 'medium',
      examples: [
        'for (let i = 0; i < array.length; i++) { /* array.length recalculated each iteration */ }',
        'const len = array.length; for (let i = 0; i < len; i++) { /* better performance */ }',
      ],
    },
    {
      id: '4',
      name: 'Inconsistent Error Handling',
      description:
        'Mixing different error handling approaches can lead to unpredictable behavior and missed errors.',
      frequency: 0.53,
      severity: 'high',
      examples: [
        'try { /* code */ } catch (e) { /* sometimes logging, sometimes throwing, sometimes ignoring */ }',
        'try { /* code */ } catch (e) { logger.error(e); throw new AppError(e); } // Consistent approach',
      ],
    },
    {
      id: '5',
      name: 'Magic Numbers',
      description:
        'Using unexplained numeric literals in code reduces readability and makes maintenance difficult.',
      frequency: 0.91,
      severity: 'low',
      examples: [
        'if (status === 200) { /* What is 200? */ }',
        'const HTTP_OK = 200; if (status === HTTP_OK) { /* Better */ }',
      ],
    },
  ]

  const filteredPatterns = mockPatterns.filter((pattern) => {
    const matchesSearch =
      pattern.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pattern.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesSeverity =
      selectedSeverity === 'all' || pattern.severity === selectedSeverity
    const matchesCategory = selectedCategory === 'all'
    return matchesSearch && matchesSeverity && matchesCategory
  })

  return (
    <div className="w-full">
      <h1 className="text-2xl font-bold mb-6">Pattern Library</h1>
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm mb-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="relative flex-grow max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <SearchIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Search patterns..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex flex-col sm:flex-row gap-4">
            <div>
              <label
                htmlFor="severity"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Severity
              </label>
              <select
                id="severity"
                className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
              >
                <option value="all">All Severities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div>
              <label
                htmlFor="category"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Category
              </label>
              <select
                id="category"
                className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                <option value="all">All Categories</option>
                <option value="security">Security</option>
                <option value="performance">Performance</option>
                <option value="maintainability">Maintainability</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {filteredPatterns.length > 0 ? (
        <PatternVisualizer patterns={filteredPatterns} />
      ) : (
        <div className="bg-white p-8 text-center rounded-lg border border-gray-200">
          <FilterIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">
            No patterns found
          </h3>
          <p className="mt-1 text-gray-500">
            Try adjusting your search or filter criteria
          </p>
        </div>
      )}
    </div>
  )
}
