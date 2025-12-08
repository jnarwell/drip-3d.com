import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DomainAwareAuthProvider, DomainAwareProtectedRoute } from './services/auth-domain';
import { UnitProvider } from './contexts/UnitContext';
import { useIsTeamDomain } from './hooks/useDomain';
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

// Company pages
import HomePage from './pages/company/HomePage';
import ProgressPage from './pages/company/ProgressPage';
import TeamPage from './pages/company/TeamPage';
import ErrorBoundary from './components/ErrorBoundary';
import TeamPortalErrorBoundary from './components/TeamPortalErrorBoundary';

import './App.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppRoutes() {
  const isTeamDomain = useIsTeamDomain();
  
  // Company site routes (www.drip-3d.com)
  if (!isTeamDomain) {
    return (
      <Routes>
        <Route path="/" element={<ErrorBoundary><HomePage /></ErrorBoundary>} />
        <Route path="/progress" element={<ErrorBoundary><ProgressPage /></ErrorBoundary>} />
        <Route path="/team" element={<ErrorBoundary><TeamPage /></ErrorBoundary>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    );
  }
  
  // Team portal routes (team.drip-3d.com)
  return (
    <TeamPortalErrorBoundary>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <DomainAwareProtectedRoute>
              <Layout />
            </DomainAwareProtectedRoute>
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
    </TeamPortalErrorBoundary>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DomainAwareAuthProvider>
        <UnitProvider>
          <Router>
            <AppRoutes />
          </Router>
        </UnitProvider>
      </DomainAwareAuthProvider>
    </QueryClientProvider>
  );
}

export default App;