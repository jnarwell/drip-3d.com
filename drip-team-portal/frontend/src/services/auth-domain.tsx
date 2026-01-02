import React, { createContext, useContext } from 'react';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { useIsTeamDomain } from '../hooks/useDomain';
import { authConfig } from './auth';

// Dev mode email - must match backend security_dev.py
const DEV_USER_EMAIL = 'user@drip-3d.com';
const DEV_USER_NAME = 'Local Developer';

// Check if running in local dev mode (localhost without Auth0 config)
const isLocalDev = () => {
  const hostname = window.location.hostname;
  const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
  const hasAuth0Config = authConfig.domain && authConfig.clientId;
  return isLocalhost && !hasAuth0Config;
};

// Mock auth context for local development
const MockAuthContext = createContext<{
  isAuthenticated: boolean;
  isLoading: boolean;
  user: { email: string; name: string } | null;
}>({
  isAuthenticated: true,
  isLoading: false,
  user: { email: DEV_USER_EMAIL, name: DEV_USER_NAME },
});

export const useMockAuth = () => useContext(MockAuthContext);

/**
 * Unified auth hook that works in both dev mode (bypasses Auth0) and production.
 * Use this instead of useAuth0() directly when you need user info.
 */
export const useDevAwareAuth = () => {
  const mockAuth = useMockAuth();
  const auth0 = useAuth0();

  // In dev mode, return mock auth; otherwise return Auth0
  if (isLocalDev()) {
    return mockAuth;
  }
  return auth0;
};

export const DomainAwareAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isTeamDomain = useIsTeamDomain();

  // Only initialize Auth0 on team domain
  if (!isTeamDomain) {
    return <>{children}</>;
  }

  // Local dev mode - bypass Auth0 entirely
  if (isLocalDev()) {
    console.log('[Auth] Running in LOCAL DEV MODE - Auth0 bypassed');
    return (
      <MockAuthContext.Provider
        value={{
          isAuthenticated: true,
          isLoading: false,
          user: { email: DEV_USER_EMAIL, name: DEV_USER_NAME },
        }}
      >
        {children}
      </MockAuthContext.Provider>
    );
  }

  // Safety check for team domain (production)
  if (!authConfig.domain || !authConfig.clientId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-yellow-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-yellow-600 mb-2">Configuration Error</h1>
          <p className="text-gray-600">Auth0 environment variables are not configured.</p>
        </div>
      </div>
    );
  }

  // Skip Auth0 callback processing on Google OAuth callback path
  // (Auth0 would try to process ?code= as its own callback and fail)
  const skipCallback = window.location.pathname === '/oauth/google/callback';

  return (
    <Auth0Provider
      domain={authConfig.domain}
      clientId={authConfig.clientId}
      authorizationParams={{
        redirect_uri: authConfig.redirectUri,
        audience: authConfig.audience,
        scope: authConfig.scope,
      }}
      skipRedirectCallback={skipCallback}
    >
      {children}
    </Auth0Provider>
  );
};

export const DomainAwareProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isTeamDomain = useIsTeamDomain();

  // Public access for company domain
  if (!isTeamDomain) {
    return <>{children}</>;
  }

  // Local dev mode - auto-authenticated
  if (isLocalDev()) {
    return <>{children}</>;
  }

  // Protected access for team domain (production)
  return <Auth0ProtectedRoute>{children}</Auth0ProtectedRoute>;
};

// Separate component to use Auth0 hook (only rendered when Auth0 is initialized)
const Auth0ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth0();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  // Check email domain for team access
  const email = user?.email || '';
  const allowedDomain = '@drip-3d.com';

  if (!email.endsWith(allowedDomain)) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-2">Access Denied</h1>
          <p className="text-gray-600">Only {allowedDomain} email addresses are allowed.</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};