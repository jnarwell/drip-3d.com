import React from 'react';
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';
import { Navigate } from 'react-router-dom';

// Debug environment variables
console.log('🔧 Auth0 Environment Variables:', {
  domain: import.meta.env.VITE_AUTH0_DOMAIN,
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID,
  audience: import.meta.env.VITE_AUTH0_AUDIENCE,
  redirectUri: window.location.origin,
});

console.log('🔧 All Available Environment Variables:');
console.table(import.meta.env);

// Check for any Auth0-related variables
const auth0Vars = Object.keys(import.meta.env)
  .filter(key => key.includes('AUTH0') || key.includes('auth0'))
  .reduce((obj: Record<string, any>, key) => {
    obj[key] = (import.meta.env as any)[key];
    return obj;
  }, {});
console.log('🔧 Found Auth0-related variables:', auth0Vars);

export const authConfig = {
  domain: import.meta.env.VITE_AUTH0_DOMAIN || '',
  clientId: import.meta.env.VITE_AUTH0_CLIENT_ID || '',
  redirectUri: window.location.origin,
  audience: import.meta.env.VITE_AUTH0_AUDIENCE || '',
  scope: "openid profile email",
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Safety check: Don't initialize Auth0 with empty values
  if (!authConfig.domain || !authConfig.clientId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-yellow-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-yellow-600 mb-2">Configuration Error</h1>
          <p className="text-gray-600">Auth0 environment variables are not configured.</p>
          <p className="text-sm text-gray-500 mt-2">
            Domain: {authConfig.domain || 'MISSING'}<br />
            Client ID: {authConfig.clientId || 'MISSING'}<br />
            Audience: {authConfig.audience || 'MISSING'}
          </p>
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

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth0();
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (!user?.email?.endsWith('@drip-3d.com')) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-red-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-2">Access Denied</h1>
          <p className="text-gray-600">This portal is restricted to @drip-3d.com email addresses</p>
        </div>
      </div>
    );
  }
  
  return <>{children}</>;
};