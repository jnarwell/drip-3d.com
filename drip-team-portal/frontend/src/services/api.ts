import axios from 'axios';
import { useAuth0 } from '@auth0/auth0-react';

// Use HTTPS for production, HTTP for localhost
const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = rawApiUrl.includes('localhost') ? rawApiUrl : rawApiUrl.replace('http://', 'https://');

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'x-email': 'test@drip-3d.com', // Dev mode authentication
  },
});

// Force HTTPS for production (but allow HTTP for localhost)
api.interceptors.request.use((config) => {
  if (config.baseURL && config.baseURL.startsWith('http://') && !config.baseURL.includes('localhost')) {
    config.baseURL = config.baseURL.replace('http://', 'https://');
  }
  if (config.url && config.url.startsWith('http://') && !config.url.includes('localhost')) {
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
    // Force HTTPS for production (but allow HTTP for localhost)
    if (config.baseURL && config.baseURL.startsWith('http://') && !config.baseURL.includes('localhost')) {
      config.baseURL = config.baseURL.replace('http://', 'https://');
    }
    if (config.url && config.url.startsWith('http://') && !config.url.includes('localhost')) {
      config.url = config.url.replace('http://', 'https://');
    }
    
    // In dev mode or Railway, use mock authentication
    if (import.meta.env.DEV || window.location.hostname.includes('railway.app')) {
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