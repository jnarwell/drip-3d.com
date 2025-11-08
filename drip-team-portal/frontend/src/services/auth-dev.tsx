import React, { createContext, useContext, useState } from 'react';

// Mock Auth0 for development
const mockUser = {
  email: 'test@drip-3d.com',
  name: 'Test User',
  sub: 'dev|123456'
};

const AuthContext = createContext<any>(null);

export const useAuth0 = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth0 must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated] = useState(true);
  const [user] = useState(mockUser);
  const [isLoading] = useState(false);

  const loginWithRedirect = () => {
    console.log('Mock login');
  };

  const logout = () => {
    console.log('Mock logout');
    window.location.href = '/';
  };

  const getAccessTokenSilently = async () => {
    return 'mock-dev-token';
  };

  const value = {
    isAuthenticated,
    user,
    isLoading,
    loginWithRedirect,
    logout,
    getAccessTokenSilently
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // In dev mode, always allow access
  return <>{children}</>;
};