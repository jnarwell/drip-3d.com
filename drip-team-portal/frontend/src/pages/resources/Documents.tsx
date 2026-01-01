import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';

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
}

// API may return paginated response or plain array
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

type ApiResponse<T> = T[] | PaginatedResponse<T>;

interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  webViewLink: string;
}

const DOC_TYPE_INFO: Record<string, { label: string; icon: string; color: string }> = {
  doc: { label: 'Document', icon: '📄', color: 'bg-blue-100 text-blue-800' },
  spreadsheet: { label: 'Spreadsheet', icon: '📊', color: 'bg-green-100 text-green-800' },
  slides: { label: 'Slides', icon: '📽️', color: 'bg-orange-100 text-orange-800' },
  pdf: { label: 'PDF', icon: '📕', color: 'bg-red-100 text-red-800' },
  paper: { label: 'Paper', icon: '📜', color: 'bg-yellow-100 text-yellow-800' },
  video: { label: 'Video', icon: '🎥', color: 'bg-purple-100 text-purple-800' },
  other: { label: 'Other', icon: '📎', color: 'bg-gray-100 text-gray-800' },
};

const Documents: React.FC = () => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBrowseModal, setShowBrowseModal] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    url: '',
    resource_type: 'doc',
    google_drive_file_id: '' as string | null,
    tags: '',
    notes: '',
  });

  // Fetch documents (resources filtered by doc types)
  const { data: documentsResponse, isLoading, error } = useQuery<ApiResponse<Resource>>({
    queryKey: ['documents'],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('type', 'doc,paper,spreadsheet,slides,pdf,video');
      const response = await api.get(`/api/v1/resources?${params.toString()}`);
      return response.data;
    },
  });

  // Extract array from paginated response or use directly if array
  const documentList = useMemo(() => {
    if (!documentsResponse) return [];
    if (Array.isArray(documentsResponse)) return documentsResponse;
    if (documentsResponse.items && Array.isArray(documentsResponse.items)) return documentsResponse.items;
    return [];
  }, [documentsResponse]);

  // Fetch Drive files for browse modal
  const { data: driveFiles, isLoading: driveLoading } = useQuery<DriveFile[]>({
    queryKey: ['drive-files'],
    queryFn: async () => {
      const response = await api.get('/api/v1/drive/files');
      return response.data;
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
    },
  });

  // Get unique tags from all documents
  const allTags = useMemo(() => {
    if (!documentList.length) return ['all'];
    const tags = new Set<string>();
    documentList.forEach(doc => doc.tags?.forEach(tag => tags.add(tag)));
    return ['all', ...Array.from(tags).sort()];
  }, [documentList]);

  // Filter documents
  const filteredDocuments = useMemo(() => {
    if (!documentList.length) return [];

    return documentList.filter(doc => {
      // Type filter
      if (selectedType !== 'all' && doc.resource_type !== selectedType) return false;

      // Tag filter
      if (selectedTag !== 'all' && !doc.tags?.includes(selectedTag)) return false;

      // Search filter
      if (searchTerm) {
        const search = searchTerm.toLowerCase();
        return (
          doc.title.toLowerCase().includes(search) ||
          doc.notes?.toLowerCase().includes(search) ||
          doc.tags?.some(tag => tag.toLowerCase().includes(search))
        );
      }

      return true;
    });
  }, [documentList, selectedType, selectedTag, searchTerm]);

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
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Documents</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setShowBrowseModal(true)}
              className="px-4 py-2 text-sm font-medium text-indigo-600 bg-white border border-indigo-600 rounded-md hover:bg-indigo-50"
            >
              Browse Drive
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
        </div>

        {/* Document Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDocuments.map(doc => {
            const typeInfo = DOC_TYPE_INFO[doc.resource_type] || DOC_TYPE_INFO.other;
            const docUrl = getResourceUrl(doc);
            return (
              <div
                key={doc.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{typeInfo.icon}</span>
                    <div>
                      {docUrl ? (
                        <a
                          href={docUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-indigo-600 hover:text-indigo-800 hover:underline"
                        >
                          {doc.title}
                        </a>
                      ) : (
                        <span className="text-sm font-medium text-gray-900">{doc.title}</span>
                      )}
                      <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${typeInfo.color}`}>
                        {typeInfo.label}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteDocument.mutate(doc.id)}
                    className="text-gray-400 hover:text-red-600 text-sm"
                  >
                    ×
                  </button>
                </div>
                {doc.notes && (
                  <p className="mt-2 text-sm text-gray-600 line-clamp-2">{doc.notes}</p>
                )}
                {doc.tags && doc.tags.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
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

        {filteredDocuments.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No documents found matching your criteria.
          </div>
        )}
      </div>

      {/* Add Document Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Add Document</h3>
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
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Browse Google Drive</h3>
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
                    <span className="text-xl">
                      {file.mimeType.includes('document') ? '📄' :
                       file.mimeType.includes('spreadsheet') ? '📊' :
                       file.mimeType.includes('presentation') ? '📽️' :
                       file.mimeType.includes('pdf') ? '📕' :
                       file.mimeType.includes('video') ? '🎥' : '📎'}
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
    </div>
  );
};

export default Documents;
