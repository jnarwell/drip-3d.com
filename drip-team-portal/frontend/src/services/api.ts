import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'x-email': 'test@drip-3d.com', // Dev mode authentication
  },
});

// Add auth token to requests
export const useAuthenticatedApi = () => {
  const authenticatedApi = axios.create({
    baseURL: API_URL,
    headers: {
      'Content-Type': 'application/json',
      'x-email': 'test@drip-3d.com', // Dev mode authentication
    },
  });

  authenticatedApi.interceptors.request.use(async (config) => {
    // In dev mode, use a mock token
    if (import.meta.env.VITE_AUTH0_DOMAIN === 'dev.auth0.com') {
      config.headers.Authorization = `Bearer mock-dev-token`;
    } else {
      // Real Auth0 implementation would go here
      try {
        // const { getAccessTokenSilently } = useAuth0();
        // const token = await getAccessTokenSilently();
        // config.headers.Authorization = `Bearer ${token}`;
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