import axios from 'axios';
import { useAuth0 } from '@auth0/auth0-react';

// Force HTTPS for production Railway deployment
const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace('http://', 'https://');

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'x-email': 'test@drip-3d.com', // Dev mode authentication
  },
});

// Force ALL requests to use HTTPS (fix for persistent Mixed Content issues)
api.interceptors.request.use((config) => {
  if (config.baseURL && config.baseURL.startsWith('http://')) {
    config.baseURL = config.baseURL.replace('http://', 'https://');
  }
  if (config.url && config.url.startsWith('http://')) {
    config.url = config.url.replace('http://', 'https://');
  }
  return config;
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
    // Force HTTPS for authenticated requests too
    if (config.baseURL && config.baseURL.startsWith('http://')) {
      config.baseURL = config.baseURL.replace('http://', 'https://');
    }
    if (config.url && config.url.startsWith('http://')) {
      config.url = config.url.replace('http://', 'https://');
    }
    
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

export const createConstant = async (constantData: {
  symbol: string;
  name: string;
  value: number;
  unit?: string;
  description?: string;
  category: string;
}) => {
  const response = await api.post('/api/v1/constants/', constantData);
  return response.data;
};

export const updateConstant = async (id: number, updateData: {
  name?: string;
  value?: number;
  unit?: string;
  description?: string;
}) => {
  const response = await api.patch(`/api/v1/constants/${id}`, updateData);
  return response.data;
};

export const deleteConstant = async (id: number) => {
  const response = await api.delete(`/api/v1/constants/${id}`);
  return response.data;
};