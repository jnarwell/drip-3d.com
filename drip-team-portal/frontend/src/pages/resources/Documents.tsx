import React, { useState, useMemo, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { useAuthenticatedApi } from '../../services/api';

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

interface GoogleConnectionStatus {
  connected: boolean;
  email?: string;
}

// Collection model from backend
interface Collection {
  id: number;
  name: string;
  description: string | null;
  color: string | null;
  resource_count: number;
  resource_ids?: number[];
  created_at: string;
}

// Predefined colors for collections
const COLLECTION_COLORS = [
  { name: 'Red', value: '#EF4444' },
  { name: 'Orange', value: '#F97316' },
  { name: 'Amber', value: '#F59E0B' },
  { name: 'Green', value: '#22C55E' },
  { name: 'Teal', value: '#14B8A6' },
  { name: 'Blue', value: '#3B82F6' },
  { name: 'Indigo', value: '#6366F1' },
  { name: 'Purple', value: '#A855F7' },
  { name: 'Pink', value: '#EC4899' },
  { name: 'Gray', value: '#6B7280' },
];

// Resource model from backend (filtered to doc types)
interface Resource {
  id: number;
  title: string;
  resource_type: string;
  url: string | null;
  google_drive_file_id: string | null;
  tags: string[];
  notes: string | null;
  component_ids: number[];
  created_at: string;
  created_by: string | null;
  is_starred: boolean;
  added_at: string | null;
}

// API may return paginated response or plain array
interface PaginatedResponse<T> {
  items?: T[];
  resources?: T[];
  total?: number;
  page?: number;
  size?: number;
}

type ApiResponse<T> = T[] | PaginatedResponse<T>;

interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  webViewLink: string;
}

const DOC_TYPE_INFO: Record<string, { label: string; icon: string; color: string }> = {
  doc: { label: 'Document', icon: 'DOC', color: 'bg-blue-100 text-blue-800' },
  spreadsheet: { label: 'Spreadsheet', icon: 'XLS', color: 'bg-green-100 text-green-800' },
  slides: { label: 'Slides', icon: 'PPT', color: 'bg-orange-100 text-orange-800' },
  pdf: { label: 'PDF', icon: 'PDF', color: 'bg-red-100 text-red-800' },
  paper: { label: 'Paper', icon: 'TXT', color: 'bg-yellow-100 text-yellow-800' },
  video: { label: 'Video', icon: 'VID', color: 'bg-purple-100 text-purple-800' },
  other: { label: 'Other', icon: 'FILE', color: 'bg-gray-100 text-gray-800' },
};

const Documents: React.FC = () => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const location = useLocation();

  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'added_at' | 'title' | 'resource_type'>('added_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showStarred, setShowStarred] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBrowseModal, setShowBrowseModal] = useState(false);
  const [driveSearchTerm, setDriveSearchTerm] = useState('');
  const [saving, setSaving] = useState(false);
  const [connectingGoogle, setConnectingGoogle] = useState(false);

  // Collection state
  const [selectedCollection, setSelectedCollection] = useState<number | null>(null);
  const [showCollectionModal, setShowCollectionModal] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null);
  const [collectionFormData, setCollectionFormData] = useState({
    name: '',
    description: '',
    color: '#3B82F6',
  });
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);
  const [addToCollectionDropdown, setAddToCollectionDropdown] = useState<number | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Bulk selection state
  const [bulkMode, setBulkMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [showBulkAddModal, setShowBulkAddModal] = useState(false);
  const [showBulkDeleteConfirm, setShowBulkDeleteConfirm] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setAddToCollectionDropdown(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Check if we just connected (from OAuth callback)
  const justConnected = location.state?.googleConnected === true;

  // Check Google Drive connection status
  const { data: googleStatus, isLoading: googleStatusLoading } = useQuery<GoogleConnectionStatus>({
    queryKey: ['google-connection-status'],
    queryFn: async () => {
      try {
        const response = await api.get('/api/v1/google-oauth/status');
        return response.data;
      } catch {
        return { connected: false };
      }
    },
    staleTime: 60000, // Cache for 1 minute
  });

  const isGoogleConnected = googleStatus?.connected || false;

  // Handle Connect Google Drive button
  const handleConnectGoogle = async () => {
    setConnectingGoogle(true);
    try {
      const response = await api.get('/api/v1/google-oauth/auth-url', {
        params: {
          redirect_uri: `${window.location.origin}/oauth/google/callback`
        }
      });
      // Redirect to Google OAuth
      window.location.href = response.data.auth_url;
    } catch (err) {
      console.error('Failed to get auth URL:', err);
      setConnectingGoogle(false);
    }
  };

  // Handle Disconnect Google Drive
  const disconnectGoogle = useMutation({
    mutationFn: async () => {
      await api.delete('/api/v1/google-oauth/disconnect');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['google-connection-status'] });
      queryClient.invalidateQueries({ queryKey: ['drive-files'] });
    },
  });

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    url: '',
    resource_type: 'doc',
    google_drive_file_id: '' as string | null,
    tags: '',
    notes: '',
  });

  // Fetch ALL documents (for tags dropdown)
  const { data: allDocumentsResponse } = useQuery<ApiResponse<Resource>>({
    queryKey: ['documents-all'],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('type', 'doc,paper,spreadsheet,slides,pdf,video');
      const response = await api.get(`/api/v1/resources?${params.toString()}`);
      return response.data;
    },
    staleTime: 60000, // Cache for 1 minute
  });

  // Fetch documents (filtered by search/type/tag/starred, sorted)
  const { data: documentsResponse, isLoading, error } = useQuery<ApiResponse<Resource>>({
    queryKey: ['documents', debouncedSearch, selectedType, selectedTag, sortBy, sortOrder, showStarred],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('type', 'doc,paper,spreadsheet,slides,pdf,video');
      if (debouncedSearch) {
        params.append('search', debouncedSearch);
      }
      if (selectedType !== 'all') {
        params.set('type', selectedType);
      }
      if (selectedTag !== 'all') {
        params.append('tag', selectedTag);
      }
      if (showStarred) {
        params.append('starred', 'true');
      }
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);
      const response = await api.get(`/api/v1/resources?${params.toString()}`);
      return response.data;
    },
  });

  // Extract array from paginated response or use directly if array
  const documentList = useMemo(() => {
    if (!documentsResponse) return [];
    if (Array.isArray(documentsResponse)) return documentsResponse;
    if (documentsResponse.resources && Array.isArray(documentsResponse.resources)) return documentsResponse.resources;
    if (documentsResponse.items && Array.isArray(documentsResponse.items)) return documentsResponse.items;
    return [];
  }, [documentsResponse]);

  // Fetch Drive files for browse modal
  const { data: driveFiles, isLoading: driveLoading } = useQuery<DriveFile[]>({
    queryKey: ['drive-files', driveSearchTerm],
    queryFn: async () => {
      const params = driveSearchTerm ? `?query=${encodeURIComponent(driveSearchTerm)}` : '';
      const response = await api.get(`/api/v1/drive/files${params}`);
      // API returns { files: [...], nextPageToken: ... }
      return response.data.files || [];
    },
    enabled: showBrowseModal,
  });

  // Create document mutation
  const createDocument = useMutation({
    mutationFn: async (docData: {
      title: string;
      resource_type: string;
      url?: string;
      google_drive_file_id?: string | null;
      tags?: string[];
      notes?: string | null;
    }) => {
      const response = await api.post('/api/v1/resources', docData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['documents-all'] });
      setShowAddModal(false);
      resetForm();
    },
  });

  // Delete document mutation
  const deleteDocument = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/v1/resources/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['documents-all'] });
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    },
  });

  const toggleStar = useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post(`/api/v1/resources/${id}/star`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['documents-all'] });
    },
  });

  // Fetch collections
  const { data: collectionsResponse, isLoading: collectionsLoading } = useQuery<{ collections: Collection[] } | Collection[]>({
    queryKey: ['collections'],
    queryFn: async () => {
      const response = await api.get('/api/v1/collections?include_resources=true');
      return response.data;
    },
  });

  // Extract collections array (API returns { collections: [...] })
  const collections = useMemo(() => {
    if (!collectionsResponse) return [];
    if (Array.isArray(collectionsResponse)) return collectionsResponse;
    if ('collections' in collectionsResponse && Array.isArray(collectionsResponse.collections)) {
      return collectionsResponse.collections;
    }
    return [];
  }, [collectionsResponse]);

  // Create collection mutation
  const createCollectionMutation = useMutation({
    mutationFn: async (data: { name: string; description?: string | null; color?: string }) => {
      const response = await api.post('/api/v1/collections', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setShowCollectionModal(false);
      resetCollectionForm();
    },
  });

  // Update collection mutation
  const updateCollectionMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: { name?: string; description?: string | null; color?: string } }) => {
      const response = await api.patch(`/api/v1/collections/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setShowCollectionModal(false);
      setEditingCollection(null);
      resetCollectionForm();
    },
  });

  // Delete collection mutation
  const deleteCollectionMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/v1/collections/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      if (selectedCollection === showDeleteConfirm) {
        setSelectedCollection(null);
      }
      setShowDeleteConfirm(null);
    },
  });

  // Add to collection mutation
  const addToCollectionMutation = useMutation({
    mutationFn: async ({ collectionId, resourceId }: { collectionId: number; resourceId: number }) => {
      const response = await api.post(`/api/v1/collections/${collectionId}/resources/${resourceId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setAddToCollectionDropdown(null);
    },
  });

  // Remove from collection mutation
  const removeFromCollectionMutation = useMutation({
    mutationFn: async ({ collectionId, resourceId }: { collectionId: number; resourceId: number }) => {
      await api.delete(`/api/v1/collections/${collectionId}/resources/${resourceId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    },
  });

  // Bulk add to collection mutation
  const bulkAddToCollectionMutation = useMutation({
    mutationFn: async ({ collectionId, resourceIds }: { collectionId: number; resourceIds: number[] }) => {
      const response = await api.post(`/api/v1/collections/${collectionId}/resources/bulk`, { resource_ids: resourceIds });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setSelectedIds(new Set());
      setBulkMode(false);
      setShowBulkAddModal(false);
    },
  });

  // Bulk delete resources mutation
  const bulkDeleteMutation = useMutation({
    mutationFn: async (ids: number[]) => {
      await api.delete('/api/v1/resources/bulk', { data: { ids } });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['documents-all'] });
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setSelectedIds(new Set());
      setBulkMode(false);
      setShowBulkDeleteConfirm(false);
    },
  });

  // Bulk selection helpers
  const toggleSelectDoc = (docId: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(docId)) {
        next.delete(docId);
      } else {
        next.add(docId);
      }
      return next;
    });
  };

  const selectAll = () => {
    setSelectedIds(new Set(filteredByCollection.map(doc => doc.id)));
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
    setBulkMode(false);
  };

  // Memoized map of document ID -> collection IDs for O(1) lookup
  const docCollectionsMap = useMemo(() => {
    const map = new Map<number, number[]>();
    collections.forEach(c => {
      c.resource_ids?.forEach(rid => {
        const existing = map.get(rid) || [];
        map.set(rid, [...existing, c.id]);
      });
    });
    return map;
  }, [collections]);

  // Get collections for a document using memoized map
  const getDocumentCollections = (docId: number): Collection[] => {
    const collectionIds = docCollectionsMap.get(docId) || [];
    return collections.filter(c => collectionIds.includes(c.id));
  };

  // Memoized filtered documents by selected collection
  const filteredByCollection = useMemo(() => {
    // Debug logging - check types
    if (selectedCollection) {
      const collection = collections.find(c => c.id === selectedCollection);
      console.log('[Debug] selectedCollection:', selectedCollection, 'type:', typeof selectedCollection);
      console.log('[Debug] collection.id:', collection?.id, 'type:', typeof collection?.id);
      console.log('[Debug] resource_ids:', collection?.resource_ids);
      console.log('[Debug] resource_ids types:', collection?.resource_ids?.map(id => typeof id));
      console.log('[Debug] doc IDs:', documentList.slice(0, 3).map(d => ({ id: d.id, type: typeof d.id })));
    }

    if (!selectedCollection) return documentList;
    const collection = collections.find(c => c.id === selectedCollection);
    if (!collection?.resource_ids || collection.resource_ids.length === 0) {
      console.log('[Debug] No resource_ids or empty - returning empty array');
      return [];
    }
    // Ensure numeric comparison
    const resourceIdSet = new Set(collection.resource_ids.map(id => Number(id)));
    const filtered = documentList.filter(doc => resourceIdSet.has(Number(doc.id)));
    console.log('[Debug] Filtered result:', filtered.length, 'of', documentList.length, 'documents');
    return filtered;
  }, [documentList, selectedCollection, collections]);

  // Reset collection form
  const resetCollectionForm = () => {
    setCollectionFormData({ name: '', description: '', color: '#3B82F6' });
  };

  // Handle collection form submit
  const handleCollectionSubmit = async () => {
    if (editingCollection) {
      await updateCollectionMutation.mutateAsync({
        id: editingCollection.id,
        data: {
          name: collectionFormData.name,
          description: collectionFormData.description || null,
          color: collectionFormData.color,
        },
      });
    } else {
      await createCollectionMutation.mutateAsync({
        name: collectionFormData.name,
        description: collectionFormData.description || null,
        color: collectionFormData.color,
      });
    }
  };

  // Open edit collection modal
  const openEditCollection = (collection: Collection) => {
    setEditingCollection(collection);
    setCollectionFormData({
      name: collection.name,
      description: collection.description || '',
      color: collection.color || '#3B82F6',
    });
    setShowCollectionModal(true);
  };

  // Extract all documents list (for tags)
  const allDocumentsList = useMemo(() => {
    if (!allDocumentsResponse) return [];
    if (Array.isArray(allDocumentsResponse)) return allDocumentsResponse;
    if (allDocumentsResponse.resources && Array.isArray(allDocumentsResponse.resources)) return allDocumentsResponse.resources;
    if (allDocumentsResponse.items && Array.isArray(allDocumentsResponse.items)) return allDocumentsResponse.items;
    return [];
  }, [allDocumentsResponse]);

  // Get unique tags from all documents
  const allTags = useMemo(() => {
    if (!allDocumentsList.length) return ['all'];
    const tags = new Set<string>();
    allDocumentsList.forEach((doc: Resource) => doc.tags?.forEach(tag => tags.add(tag)));
    return ['all', ...Array.from(tags).sort()];
  }, [allDocumentsList]);

  const resetForm = () => {
    setFormData({
      title: '',
      url: '',
      resource_type: 'doc',
      google_drive_file_id: null,
      tags: '',
      notes: '',
    });
  };

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await createDocument.mutateAsync({
        title: formData.title,
        resource_type: formData.resource_type,
        url: formData.url || undefined,
        google_drive_file_id: formData.google_drive_file_id || undefined,
        tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
        notes: formData.notes || null,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDriveFileSelect = (file: DriveFile) => {
    // Infer resource type from MIME type
    let resourceType = 'other';
    if (file.mimeType.includes('document')) resourceType = 'doc';
    else if (file.mimeType.includes('spreadsheet')) resourceType = 'spreadsheet';
    else if (file.mimeType.includes('presentation')) resourceType = 'slides';
    else if (file.mimeType.includes('pdf')) resourceType = 'pdf';
    else if (file.mimeType.includes('video')) resourceType = 'video';

    setFormData({
      ...formData,
      title: file.name,
      url: file.webViewLink,
      resource_type: resourceType,
      google_drive_file_id: file.id,
    });
    setShowBrowseModal(false);
    setShowAddModal(true);
  };

  // Get display URL for a resource
  const getResourceUrl = (doc: Resource): string | null => {
    if (doc.url) return doc.url;
    if (doc.google_drive_file_id) {
      return `https://drive.google.com/file/d/${doc.google_drive_file_id}/view`;
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-red-600">
          <h3 className="text-lg font-semibold mb-2">Error</h3>
          <p>Failed to load documents</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Success message after connecting */}
      {justConnected && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3">
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-green-800">Google Drive connected successfully!</span>
        </div>
      )}

      {/* Google Drive Connection Banner */}
      {!googleStatusLoading && !isGoogleConnected && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg className="w-8 h-8 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.24 8.79l-4.79 8.3h9.58l-4.79-8.3zm0-2.62L19.46 18H4.98L12.24 6.17zM22 18l-9.76-16.9L2.24 18H22z"/>
              </svg>
              <div>
                <p className="font-medium text-blue-900">Connect Google Drive</p>
                <p className="text-sm text-blue-700">Browse and link files directly from your Google Drive</p>
              </div>
            </div>
            <button
              onClick={handleConnectGoogle}
              disabled={connectingGoogle}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {connectingGoogle ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Connecting...
                </>
              ) : (
                'Connect Drive'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Mobile sidebar toggle */}
      <div className="md:hidden mb-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="flex items-center gap-2 px-4 py-2 bg-white shadow rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
          aria-label={sidebarOpen ? "Close collections sidebar" : "Open collections sidebar"}
          aria-expanded={sidebarOpen}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          Collections ({collections.length})
          <svg className={`w-4 h-4 transition-transform ${sidebarOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Collections Sidebar - hidden on mobile unless toggled */}
        <div className={`w-full md:w-64 flex-shrink-0 ${sidebarOpen ? 'block' : 'hidden'} md:block`}>
          <div className="bg-white shadow rounded-lg p-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-semibold text-gray-900">Collections</h3>
              <button
                onClick={() => { resetCollectionForm(); setEditingCollection(null); setShowCollectionModal(true); }}
                className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                aria-label="Create new collection"
              >
                + New
              </button>
            </div>
            <div className="space-y-1">
              <button
                onClick={() => setSelectedCollection(null)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center justify-between ${
                  selectedCollection === null ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-gray-50 text-gray-700'
                }`}
              >
                <span>All Documents</span>
                <span className="text-xs text-gray-500">{allDocumentsList.length}</span>
              </button>
              {collectionsLoading ? (
                <div className="animate-pulse space-y-2 mt-2">
                  <div className="h-8 bg-gray-200 rounded" />
                  <div className="h-8 bg-gray-200 rounded" />
                  <div className="h-8 bg-gray-200 rounded" />
                </div>
              ) : (
                collections.map(collection => (
                  <div key={collection.id} className="group relative">
                    <button
                      onClick={() => setSelectedCollection(collection.id)}
                      className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 ${
                        selectedCollection === collection.id ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <span
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: collection.color || '#6B7280' }}
                      />
                      <span className="truncate flex-1">{collection.name}</span>
                      <span className="text-xs text-gray-500">{collection.resource_count}</span>
                    </button>
                    <div className="absolute right-1 top-1/2 -translate-y-1/2 hidden group-hover:flex gap-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); openEditCollection(collection); }}
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Edit collection"
                        aria-label={`Edit collection ${collection.name}`}
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); setShowDeleteConfirm(collection.id); }}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Delete collection"
                        aria-label={`Delete collection ${collection.name}`}
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-4">
              <h2 className="text-2xl font-bold text-gray-900">
                {selectedCollection
                  ? collections.find(c => c.id === selectedCollection)?.name || 'Documents'
                  : 'Documents'}
              </h2>
              {isGoogleConnected && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12.24 8.79l-4.79 8.3h9.58l-4.79-8.3zm0-2.62L19.46 18H4.98L12.24 6.17zM22 18l-9.76-16.9L2.24 18H22z"/>
                  </svg>
                  Drive Connected
                </span>
              )}
            </div>
            <div className="flex gap-2">
              {isGoogleConnected && (
                <>
                  <button
                    onClick={() => { setDriveSearchTerm(''); setShowBrowseModal(true); }}
                    className="px-4 py-2 text-sm font-medium text-indigo-600 bg-white border border-indigo-600 rounded-md hover:bg-indigo-50"
                  >
                    Browse Drive
                  </button>
                  <button
                    onClick={() => disconnectGoogle.mutate()}
                    className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:text-red-600"
                    title="Disconnect Google Drive"
                    aria-label="Disconnect Google Drive"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                  </button>
                </>
              )}
              <button
                onClick={() => { setBulkMode(!bulkMode); if (bulkMode) setSelectedIds(new Set()); }}
                className={`px-4 py-2 text-sm font-medium rounded-md border ${
                  bulkMode
                    ? 'bg-indigo-100 text-indigo-700 border-indigo-300'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {bulkMode ? 'Cancel Select' : 'Select'}
              </button>
              <button
                onClick={() => { resetForm(); setShowAddModal(true); }}
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700"
              >
                Add Document
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="mb-6 space-y-4 sm:space-y-0 sm:flex sm:gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by title, notes, or tags..."
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div className="sm:w-40">
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="all">All Types</option>
                {Object.entries(DOC_TYPE_INFO).map(([key, info]) => (
                  <option key={key} value={key}>{info.label}</option>
                ))}
              </select>
            </div>
            <div className="sm:w-40">
              <select
                value={selectedTag}
                onChange={(e) => setSelectedTag(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                {allTags.map(tag => (
                  <option key={tag} value={tag}>
                    {tag === 'all' ? 'All Tags' : tag}
                  </option>
                ))}
              </select>
            </div>
            {/* Sort dropdown */}
            <div className="sm:w-44">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'added_at' | 'title' | 'resource_type')}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="added_at">Date Added</option>
                <option value="title">Name</option>
                <option value="resource_type">Type</option>
              </select>
            </div>
            {/* Sort order toggle */}
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
            >
              {sortOrder === 'asc' ? (
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                </svg>
              )}
            </button>
            {/* Starred filter */}
            <button
              onClick={() => setShowStarred(!showStarred)}
              className={`px-3 py-2 border rounded-md flex items-center gap-1.5 ${
                showStarred
                  ? 'bg-yellow-50 border-yellow-300 text-yellow-700'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
              title={showStarred ? 'Showing starred only' : 'Show all'}
            >
              <svg className="w-5 h-5" fill={showStarred ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
              <span className="text-sm font-medium">Starred</span>
            </button>
          </div>

          {/* Bulk mode select all bar */}
          {bulkMode && (
            <div className="mb-4 flex items-center gap-4 p-3 bg-indigo-50 rounded-lg">
              <button
                onClick={selectAll}
                className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
              >
                Select All ({filteredByCollection.length})
              </button>
              <span className="text-sm text-gray-600">
                {selectedIds.size} selected
              </span>
            </div>
          )}

          {/* Document Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredByCollection.map(doc => {
              const typeInfo = DOC_TYPE_INFO[doc.resource_type] || DOC_TYPE_INFO.other;
              const docUrl = getResourceUrl(doc);
              const docCollections = getDocumentCollections(doc.id);
              const isSelected = selectedIds.has(doc.id);
              return (
                <div
                  key={doc.id}
                  className={`border rounded-lg p-4 hover:shadow-md transition-shadow ${
                    isSelected ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200'
                  }`}
                  onClick={bulkMode ? () => toggleSelectDoc(doc.id) : undefined}
                  style={bulkMode ? { cursor: 'pointer' } : undefined}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      {bulkMode && (
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectDoc(doc.id)}
                          onClick={(e) => e.stopPropagation()}
                          className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 flex-shrink-0"
                          aria-label={`Select ${doc.title}`}
                        />
                      )}
                      <div className="min-w-0">
                        {docUrl ? (
                          <a
                            href={docUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-medium text-indigo-600 hover:text-indigo-800 hover:underline block truncate"
                          >
                            {doc.title}
                          </a>
                        ) : (
                          <span className="text-sm font-medium text-gray-900 block truncate">{doc.title}</span>
                        )}
                        <span className={`inline-block mt-0.5 px-2 py-0.5 text-xs rounded-full ${typeInfo.color}`}>
                          {typeInfo.label}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                      {/* Star toggle */}
                      <button
                        onClick={(e) => { e.stopPropagation(); toggleStar.mutate(doc.id); }}
                        className={`p-1 ${doc.is_starred ? 'text-yellow-500' : 'text-gray-400 hover:text-yellow-500'}`}
                        title={doc.is_starred ? 'Remove from starred' : 'Add to starred'}
                      >
                        <svg className="w-4 h-4" fill={doc.is_starred ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                        </svg>
                      </button>
                      {/* Add to Collection dropdown */}
                      <div className="relative" ref={addToCollectionDropdown === doc.id ? dropdownRef : undefined}>
                        <button
                          onClick={() => setAddToCollectionDropdown(addToCollectionDropdown === doc.id ? null : doc.id)}
                          className="p-1 text-gray-400 hover:text-indigo-600"
                          title="Add to collection"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                          </svg>
                        </button>
                        {addToCollectionDropdown === doc.id && (
                          <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                            <div className="py-1">
                              {collections.length === 0 ? (
                                <div className="px-3 py-2 text-sm text-gray-500">No collections yet</div>
                              ) : (
                                collections.map(collection => {
                                  const isInCollection = collection.resource_ids?.includes(doc.id);
                                  return (
                                    <button
                                      key={collection.id}
                                      onClick={() => {
                                        if (isInCollection) {
                                          removeFromCollectionMutation.mutate({ collectionId: collection.id, resourceId: doc.id });
                                        } else {
                                          addToCollectionMutation.mutate({ collectionId: collection.id, resourceId: doc.id });
                                        }
                                      }}
                                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
                                    >
                                      <span
                                        className="w-3 h-3 rounded-full flex-shrink-0"
                                        style={{ backgroundColor: collection.color || '#6B7280' }}
                                      />
                                      <span className="truncate flex-1">{collection.name}</span>
                                      {isInCollection && (
                                        <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                        </svg>
                                      )}
                                    </button>
                                  );
                                })
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => deleteDocument.mutate(doc.id)}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Delete document"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                  {/* Collection badges */}
                  {docCollections.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {docCollections.map(collection => (
                        <span
                          key={collection.id}
                          className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full"
                          style={{
                            backgroundColor: `${collection.color}20` || '#6B728020',
                            color: collection.color || '#6B7280'
                          }}
                        >
                          <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ backgroundColor: collection.color || '#6B7280' }}
                          />
                          {collection.name}
                        </span>
                      ))}
                    </div>
                  )}
                  {doc.notes && (
                    <p className="mt-2 text-sm text-gray-600 line-clamp-2">{doc.notes}</p>
                  )}
                  {doc.tags && doc.tags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {doc.tags.map(tag => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {filteredByCollection.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No documents found matching your criteria.
            </div>
          )}
        </div>
      </div>

      {/* Add Document Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="add-doc-title">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 id="add-doc-title" className="text-lg font-medium text-gray-900 mb-4">Add Document</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">URL (Google Drive link)</label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  placeholder="https://docs.google.com/..."
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
                {formData.google_drive_file_id && (
                  <p className="mt-1 text-xs text-green-600">
                    Linked to Drive file: {formData.google_drive_file_id}
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Type</label>
                <select
                  value={formData.resource_type}
                  onChange={(e) => setFormData({ ...formData, resource_type: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                >
                  {Object.entries(DOC_TYPE_INFO).map(([key, info]) => (
                    <option key={key} value={key}>{info.icon} {info.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Tags (comma-separated)</label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  placeholder="mechanical, design, specs"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={saving || !formData.title || (!formData.url && !formData.google_drive_file_id)}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Adding...' : 'Add'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Browse Drive Modal */}
      {showBrowseModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="browse-drive-title">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
            <h3 id="browse-drive-title" className="text-lg font-medium text-gray-900 mb-4">Browse Google Drive</h3>
            <input
              type="text"
              value={driveSearchTerm}
              onChange={(e) => setDriveSearchTerm(e.target.value)}
              placeholder="Search files..."
              className="mb-4 w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
            {driveLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
                {driveFiles?.map(file => (
                  <button
                    key={file.id}
                    onClick={() => handleDriveFileSelect(file)}
                    className="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center gap-3"
                  >
                    <span className="text-xs font-bold text-gray-500">
                      {file.mimeType.includes('document') ? 'DOC' :
                       file.mimeType.includes('spreadsheet') ? 'XLS' :
                       file.mimeType.includes('presentation') ? 'PPT' :
                       file.mimeType.includes('pdf') ? 'PDF' :
                       file.mimeType.includes('video') ? 'VID' : 'FILE'}
                    </span>
                    <span className="text-sm text-gray-900 truncate">{file.name}</span>
                  </button>
                ))}
                {(!driveFiles || driveFiles.length === 0) && (
                  <div className="text-center py-8 text-gray-500">
                    No files found in Drive
                  </div>
                )}
              </div>
            )}
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setShowBrowseModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Collection Modal (Create/Edit) */}
      {showCollectionModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="collection-modal-title">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 id="collection-modal-title" className="text-lg font-medium text-gray-900 mb-4">
              {editingCollection ? 'Edit Collection' : 'New Collection'}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={collectionFormData.name}
                  onChange={(e) => setCollectionFormData({ ...collectionFormData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="e.g., Project Alpha Docs"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description (optional)</label>
                <textarea
                  value={collectionFormData.description}
                  onChange={(e) => setCollectionFormData({ ...collectionFormData, description: e.target.value })}
                  rows={2}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Brief description of this collection"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
                <div className="flex flex-wrap gap-2">
                  {COLLECTION_COLORS.map(color => (
                    <button
                      key={color.value}
                      type="button"
                      onClick={() => setCollectionFormData({ ...collectionFormData, color: color.value })}
                      className={`w-8 h-8 rounded-full border-2 transition-all ${
                        collectionFormData.color === color.value
                          ? 'border-gray-900 scale-110'
                          : 'border-transparent hover:border-gray-300'
                      }`}
                      style={{ backgroundColor: color.value }}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => { setShowCollectionModal(false); setEditingCollection(null); resetCollectionForm(); }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCollectionSubmit}
                disabled={!collectionFormData.name.trim() || createCollectionMutation.isPending || updateCollectionMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createCollectionMutation.isPending || updateCollectionMutation.isPending
                  ? 'Saving...'
                  : editingCollection ? 'Save Changes' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Collection Confirmation */}
      {showDeleteConfirm !== null && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50" role="alertdialog" aria-modal="true" aria-labelledby="delete-confirm-title" aria-describedby="delete-confirm-desc">
          <div className="bg-white rounded-lg p-6 w-full max-w-sm">
            <h3 id="delete-confirm-title" className="text-lg font-medium text-gray-900 mb-2">Delete Collection</h3>
            <p id="delete-confirm-desc" className="text-sm text-gray-600 mb-4">
              Are you sure you want to delete "{collections.find(c => c.id === showDeleteConfirm)?.name}"?
              Documents in this collection will not be deleted.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteCollectionMutation.mutate(showDeleteConfirm)}
                disabled={deleteCollectionMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {deleteCollectionMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Action Floating Bar */}
      {bulkMode && selectedIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white rounded-lg shadow-xl px-6 py-3 flex items-center gap-4 z-40">
          <span className="text-sm font-medium">
            {selectedIds.size} selected
          </span>
          <div className="w-px h-6 bg-gray-600" />
          <button
            onClick={() => setShowBulkAddModal(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Add to Collection
          </button>
          <button
            onClick={() => setShowBulkDeleteConfirm(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-red-600 hover:bg-red-700 rounded-md transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete
          </button>
          <button
            onClick={clearSelection}
            className="px-3 py-1.5 text-sm font-medium text-gray-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Bulk Add to Collection Modal */}
      {showBulkAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="bulk-add-title">
          <div className="bg-white rounded-lg p-6 w-full max-w-sm">
            <h3 id="bulk-add-title" className="text-lg font-medium text-gray-900 mb-4">
              Add {selectedIds.size} documents to collection
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {collections.length === 0 ? (
                <p className="text-sm text-gray-500 py-4 text-center">
                  No collections yet. Create one first.
                </p>
              ) : (
                collections.map(collection => (
                  <button
                    key={collection.id}
                    onClick={() => bulkAddToCollectionMutation.mutate({
                      collectionId: collection.id,
                      resourceIds: Array.from(selectedIds)
                    })}
                    disabled={bulkAddToCollectionMutation.isPending}
                    className="w-full text-left px-4 py-3 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 flex items-center gap-3 transition-colors disabled:opacity-50"
                  >
                    <span
                      className="w-4 h-4 rounded-full flex-shrink-0"
                      style={{ backgroundColor: collection.color || '#6B7280' }}
                    />
                    <span className="text-sm font-medium text-gray-900 flex-1">{collection.name}</span>
                    <span className="text-xs text-gray-500">{collection.resource_count} docs</span>
                  </button>
                ))
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setShowBulkAddModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={bulkAddToCollectionMutation.isPending}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bulk Delete Confirmation Modal */}
      {showBulkDeleteConfirm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50" role="alertdialog" aria-modal="true" aria-labelledby="bulk-delete-title" aria-describedby="bulk-delete-desc">
          <div className="bg-white rounded-lg p-6 w-full max-w-sm">
            <h3 id="bulk-delete-title" className="text-lg font-medium text-gray-900 mb-2">Delete Documents</h3>
            <p id="bulk-delete-desc" className="text-sm text-gray-600 mb-4">
              Are you sure you want to delete {selectedIds.size} document{selectedIds.size !== 1 ? 's' : ''}?
              This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowBulkDeleteConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={bulkDeleteMutation.isPending}
              >
                Cancel
              </button>
              <button
                onClick={() => bulkDeleteMutation.mutate(Array.from(selectedIds))}
                disabled={bulkDeleteMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {bulkDeleteMutation.isPending ? 'Deleting...' : `Delete ${selectedIds.size} Documents`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Documents;
