import React from 'react';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';
import { useIsTeamDomain } from '../hooks/useDomain';
import { authConfig } from './auth';

export const DomainAwareAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isTeamDomain = useIsTeamDomain();
  
  // Only initialize Auth0 on team domain
  if (!isTeamDomain) {
    return <>{children}</>;
  }

  // Safety check for team domain
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

  return (
    <Auth0Provider
      domain={authConfig.domain}
      clientId={authConfig.clientId}
      authorizationParams={{
        redirect_uri: authConfig.redirectUri,
        audience: authConfig.audience,
        scope: authConfig.scope,
      }}
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
  
  // Protected access for team domain
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