import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, ProtectedRoute } from './services/auth-dev';
import { UnitProvider } from './contexts/UnitContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ComponentRegistry from './pages/ComponentRegistry';
import ComponentDetailPage from './pages/ComponentDetailPage';
import TestCampaign from './pages/TestCampaign';
import Reports from './pages/Reports';
import Login from './pages/Login';
import Settings from './pages/Settings';
import Resources from './pages/Resources';
import PropertyTables from './pages/resources/PropertyTables';
import Constants from './pages/resources/Constants';
import Templates from './pages/resources/Templates';
import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <UnitProvider>
          <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="components" element={<ComponentRegistry />} />
              <Route path="components/:componentId" element={<ComponentDetailPage />} />
              <Route path="tests" element={<TestCampaign />} />
              <Route path="reports" element={<Reports />} />
              <Route path="settings" element={<Settings />} />
              <Route path="resources" element={<Resources />}>
                <Route index element={<Navigate to="/resources/property-tables" />} />
                <Route path="property-tables" element={<PropertyTables />} />
                <Route path="constants" element={<Constants />} />
                <Route path="templates" element={<Templates />} />
              </Route>
            </Route>
          </Routes>
        </Router>
        </UnitProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
