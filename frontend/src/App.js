import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';
import HomePage from './pages/HomePage';
import BillsPage from './pages/BillsPage';
import BillDetailPage from './pages/BillDetailPage';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import CategoryPage from './pages/CategoryPage';
import IntegrationsPage from './pages/IntegrationsPage';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/bills" element={
                <ProtectedRoute>
                  <BillsPage />
                </ProtectedRoute>
              } />
              <Route path="/bills/:id" element={
                <ProtectedRoute>
                  <BillDetailPage />
                </ProtectedRoute>
              } />
              <Route path="/analytics" element={
                <ProtectedRoute>
                  <AnalyticsDashboard />
                </ProtectedRoute>
              } />
              <Route path="/categorize" element={
                <ProtectedRoute>
                  <CategoryPage />
                </ProtectedRoute>
              } />
              <Route path="/integrations" element={
                <ProtectedRoute>
                  <IntegrationsPage />
                </ProtectedRoute>
              } />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App; 