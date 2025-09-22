import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout/Layout'
import { AuthProvider } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import GoogleOAuthProvider from './components/providers/GoogleOAuthProvider'
import NotificationManager from './components/NotificationManager'
import ProtectedRoute from './components/ProtectedRoute'
import { Home } from './pages/Home'
import { CodeReview } from './pages/CodeReview'
import { PatternLibrary } from './pages/PatternLibrary'
import { Settings } from './pages/Settings'
import { Profile } from './pages/Profile'
import { Login } from './pages/Login'
import { LoginSimple } from './pages/LoginSimple'
import { Signup } from './pages/Signup'
import { MonacoEditorTest } from './components/MonacoEditorTest'
import { MonacoEditorDemo } from './components/MonacoEditorDemo'
import { ApiTest } from './pages/ApiTest'
import { NotificationDemo } from './pages/NotificationDemo'
export function App() {
  return (
    <GoogleOAuthProvider>
      <NotificationProvider>
        <AuthProvider>
          <Router>
            <Routes>
              {/* Public auth routes */}
              <Route path="/login" element={<LoginSimple />} />
              <Route path="/login-oauth" element={<Login />} />
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
                <Route path="/notification-demo" element={<NotificationDemo />} />
              </Route>
            </Routes>
            <NotificationManager />
          </Router>
        </AuthProvider>
      </NotificationProvider>
    </GoogleOAuthProvider>
  )
}
export default App
