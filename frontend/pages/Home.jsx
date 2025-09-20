import React from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRightIcon,
  CodeIcon,
  BrainIcon,
  LineChartIcon,
  ShieldIcon,
} from 'lucide-react'
export function Home() {
  return (
    <div className="w-full">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-indigo-600 to-purple-600 py-16 px-4 sm:px-6 lg:px-8 text-white rounded-lg shadow-lg mb-12">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-6">
            Intelligent Code Review with Pattern Learning
          </h1>
          <p className="text-xl mb-8">
            Powered by Google Gemini, our AI-driven code review system learns
            from patterns to provide smarter, more consistent feedback.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              to="/code-review"
              className="bg-white text-indigo-600 hover:bg-gray-100 px-6 py-3 rounded-md font-medium flex items-center justify-center"
            >
              Start Review
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </Link>
            <Link
              to="/pattern-library"
              className="bg-indigo-700 hover:bg-indigo-800 px-6 py-3 rounded-md font-medium"
            >
              Explore Patterns
            </Link>
          </div>
        </div>
      </section>
      {/* Features Section */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Key Features
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <CodeIcon className="h-6 w-6 text-indigo-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">
              Intelligent Code Analysis
            </h3>
            <p className="text-gray-600">
              Our AI reviews your code for bugs, anti-patterns, and optimization
              opportunities with high accuracy.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <BrainIcon className="h-6 w-6 text-indigo-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Pattern Learning</h3>
            <p className="text-gray-600">
              The system learns from code patterns across projects to provide
              increasingly relevant recommendations.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <LineChartIcon className="h-6 w-6 text-indigo-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Detailed Analytics</h3>
            <p className="text-gray-600">
              Track your code quality improvements over time with comprehensive
              analytics dashboards.
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
              <ShieldIcon className="h-6 w-6 text-indigo-600" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Security Scanning</h3>
            <p className="text-gray-600">
              Identify potential security vulnerabilities and receive actionable
              remediation guidance.
            </p>
          </div>
        </div>
      </section>
      {/* Call to Action */}
      <section className="bg-gray-50 rounded-lg p-8 text-center mt-12">
        <h2 className="text-2xl font-bold mb-4">
          Ready to improve your code quality?
        </h2>
        <p className="text-lg text-gray-600 mb-6 max-w-2xl mx-auto">
          Start using our intelligent code review system today and watch your
          code quality improve with every commit.
        </p>
        <Link
          to="/code-review"
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-md font-medium"
        >
          Get Started
        </Link>
      </section>
    </div>
  )
}
