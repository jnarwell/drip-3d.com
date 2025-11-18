import axios from 'axios';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Debug API URL
console.log('🔧 API_URL being used:', API_URL);
console.log('🔧 VITE_API_URL from env:', import.meta.env.VITE_API_URL);

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'x-email': 'test@drip-3d.com', // Dev mode authentication
  },
});

// Add auth token to requests
export const useAuthenticatedApi = () => {
  const { getAccessTokenSilently, user } = useAuth0();

  const authenticatedApi = axios.create({
    baseURL: API_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  authenticatedApi.interceptors.request.use(async (config) => {
    // In dev mode, use mock authentication
    if (import.meta.env.DEV) {
      config.headers['x-email'] = 'test@drip-3d.com';
      config.headers.Authorization = `Bearer mock-dev-token`;
    } else {
      // Production Auth0 implementation
      try {
        const token = await getAccessTokenSilently({
          authorizationParams: {
            audience: import.meta.env.VITE_AUTH0_AUDIENCE,
          },
        });
        config.headers.Authorization = `Bearer ${token}`;
        if (user?.email) {
          config.headers['x-email'] = user.email;
        }
      } catch (error) {
        console.error('Error getting access token:', error);
      }
    }
    return config;
  });

  return authenticatedApi;
};

// Resources API functions
export const getConstants = async (category?: string, search?: string) => {
  const params = new URLSearchParams();
  if (category && category !== 'all') {
    params.append('category', category);
  }
  if (search) {
    params.append('search', search);
  }
  const response = await api.get(`/api/v1/constants${params.toString() ? `?${params}` : ''}`);
  return response.data;
};