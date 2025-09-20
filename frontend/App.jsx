import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout/Layout'
import { AuthLayout } from './components/Layout/AuthLayout'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import { Home } from './pages/Home'
import { CodeReview } from './pages/CodeReview'
import { PatternLibrary } from './pages/PatternLibrary'
import { Settings } from './pages/Settings'
import { Profile } from './pages/Profile'
import { Login } from './pages/Login'
import { Signup } from './pages/Signup'
import { MonacoEditorTest } from './components/MonacoEditorTest'
import { MonacoEditorDemo } from './components/MonacoEditorDemo'
import { ApiTest } from './pages/ApiTest'
export function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public auth routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          
          {/* Protected app routes with main Layout */}
          <Route element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route path="/" element={<Home />} />
            <Route path="/code-review" element={<CodeReview />} />
            <Route path="/pattern-library" element={<PatternLibrary />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/monaco-test" element={<MonacoEditorTest />} />
            <Route path="/monaco-demo" element={<MonacoEditorDemo />} />
            <Route path="/api-test" element={<ApiTest />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  )
}
export default App
