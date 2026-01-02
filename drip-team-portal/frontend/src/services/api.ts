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
    
    // In local dev mode only, use mock authentication
    if (import.meta.env.DEV) {
      config.headers['x-email'] = 'user@drip-3d.com';
      config.headers.Authorization = `Bearer mock-dev-token`;
    } else {
      // Production Auth0 implementation (team.drip-3d.com, Railway, etc.)
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

// Contacts API functions
export const getContacts = async (filter?: 'all' | 'internal' | 'external', search?: string) => {
  const params = new URLSearchParams();
  if (filter && filter !== 'all') {
    params.append('is_internal', filter === 'internal' ? 'true' : 'false');
  }
  if (search) {
    params.append('search', search);
  }
  const response = await api.get(`/api/v1/contacts${params.toString() ? `?${params}` : ''}`);
  return response.data;
};

export const createContact = async (contactData: {
  name: string;
  organization?: string | null;
  expertise?: string[];
  email: string;
  secondary_email?: string | null;
  phone?: string | null;
  notes?: string | null;
  is_internal?: boolean;
}) => {
  const response = await api.post('/api/v1/contacts', contactData);
  return response.data;
};

export const updateContact = async (id: number, updateData: {
  name?: string;
  organization?: string | null;
  expertise?: string[];
  email?: string;
  secondary_email?: string | null;
  phone?: string | null;
  notes?: string | null;
  is_internal?: boolean;
}) => {
  const response = await api.patch(`/api/v1/contacts/${id}`, updateData);
  return response.data;
};

export const deleteContact = async (id: number) => {
  const response = await api.delete(`/api/v1/contacts/${id}`);
  return response.data;
};

// Documents API functions (uses existing /resources endpoint filtered by doc types)
export const getDocuments = async (type?: string, tag?: string, search?: string) => {
  const params = new URLSearchParams();
  // Filter to document-type resources
  params.append('type', 'doc,paper,spreadsheet,slides,pdf,video');
  if (type && type !== 'all') {
    params.set('type', type);
  }
  if (tag && tag !== 'all') {
    params.append('tag', tag);
  }
  if (search) {
    params.append('search', search);
  }
  const response = await api.get(`/api/v1/resources?${params.toString()}`);
  return response.data;
};

export const createDocument = async (docData: {
  title: string;
  resource_type: string;
  url?: string;
  google_drive_file_id?: string;
  tags?: string[];
  notes?: string | null;
  component_ids?: number[];
}) => {
  const response = await api.post('/api/v1/resources', docData);
  return response.data;
};

export const updateDocument = async (id: number, updateData: {
  title?: string;
  resource_type?: string;
  url?: string;
  google_drive_file_id?: string;
  tags?: string[];
  notes?: string | null;
  component_ids?: number[];
}) => {
  const response = await api.patch(`/api/v1/resources/${id}`, updateData);
  return response.data;
};

export const deleteDocument = async (id: number) => {
  const response = await api.delete(`/api/v1/resources/${id}`);
  return response.data;
};

// Google Drive API functions
export const getDriveFiles = async () => {
  const response = await api.get('/api/v1/drive/files');
  return response.data;
};

export const getDriveFile = async (fileId: string) => {
  const response = await api.get(`/api/v1/drive/files/${fileId}`);
  return response.data;
};

// Google OAuth API functions
export const getGoogleAuthUrl = async (redirectUri: string) => {
  const response = await api.get('/api/v1/google-oauth/auth-url', {
    params: { redirect_uri: redirectUri }
  });
  return response.data;
};

export const postGoogleCallback = async (code: string, state?: string, redirectUri?: string) => {
  const response = await api.post('/api/v1/google-oauth/callback', {
    code,
    state,
    redirect_uri: redirectUri,
  });
  return response.data;
};

export const getGoogleConnectionStatus = async () => {
  const response = await api.get('/api/v1/google-oauth/status');
  return response.data;
};

export const disconnectGoogle = async () => {
  const response = await api.delete('/api/v1/google-oauth/disconnect');
  return response.data;
};