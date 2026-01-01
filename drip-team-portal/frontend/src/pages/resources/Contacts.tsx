import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';

interface Contact {
  id: number;
  name: string;
  organization: string | null;
  expertise: string[];
  email: string;
  secondary_email: string | null;
  phone: string | null;
  notes: string | null;
  is_internal: boolean;
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

const Contacts: React.FC = () => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'internal' | 'external'>('all');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [sortConfig, setSortConfig] = useState<{
    key: keyof Contact;
    direction: 'asc' | 'desc';
  }>({ key: 'name', direction: 'asc' });

  // Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [deletingContact, setDeletingContact] = useState<Contact | null>(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    organization: '',
    expertise: '',
    email: '',
    secondary_email: '',
    phone: '',
    notes: '',
    is_internal: false,
  });

  // Validation error state
  const [formError, setFormError] = useState<string | null>(null);

  // Copy feedback state
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Copy to clipboard helper
  const copyToClipboard = async (text: string, fieldId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(fieldId);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Format phone number: 4157414741 → 415-741-4741
  const formatPhone = (phone: string): string => {
    const digits = phone.replace(/\D/g, '');
    if (digits.length === 10) {
      return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
    }
    if (digits.length === 11 && digits[0] === '1') {
      return `+1 ${digits.slice(1, 4)}-${digits.slice(4, 7)}-${digits.slice(7)}`;
    }
    return phone; // Return as-is if can't format
  };

  // Fetch contacts
  const { data: contactsResponse, isLoading, error } = useQuery<ApiResponse<Contact>>({
    queryKey: ['contacts'],
    queryFn: async () => {
      const response = await api.get('/api/v1/contacts');
      return response.data;
    },
  });

  // Extract array from paginated response or use directly if array
  // API returns { contacts: [...], total, limit, offset }
  const contactList = useMemo(() => {
    if (!contactsResponse) return [];
    if (Array.isArray(contactsResponse)) return contactsResponse;
    const resp = contactsResponse as { contacts?: Contact[]; items?: Contact[] };
    if (resp.contacts && Array.isArray(resp.contacts)) return resp.contacts;
    if (resp.items && Array.isArray(resp.items)) return resp.items;
    return [];
  }, [contactsResponse]);

  // Create contact mutation
  const createContact = useMutation({
    mutationFn: async (contactData: Omit<Contact, 'id' | 'created_at' | 'created_by'>) => {
      const response = await api.post('/api/v1/contacts', contactData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setShowAddModal(false);
      resetForm();
    },
  });

  // Update contact mutation
  const updateContact = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Contact> }) => {
      const response = await api.patch(`/api/v1/contacts/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setShowEditModal(false);
      setEditingContact(null);
      resetForm();
    },
  });

  // Delete contact mutation
  const deleteContact = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/api/v1/contacts/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
      setShowDeleteModal(false);
      setDeletingContact(null);
    },
  });

  // Filter and sort contacts
  const filteredAndSortedContacts = useMemo(() => {
    if (!contactList.length) return [];

    let filtered = contactList;

    // Type filter
    if (filterType === 'internal') {
      filtered = filtered.filter(c => c.is_internal);
    } else if (filterType === 'external') {
      filtered = filtered.filter(c => !c.is_internal);
    }

    // Search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(c =>
        c.name.toLowerCase().includes(search) ||
        c.organization?.toLowerCase().includes(search) ||
        c.expertise?.some(e => e.toLowerCase().includes(search))
      );
    }

    // Sort
    return [...filtered].sort((a, b) => {
      const aVal = a[sortConfig.key];
      const bVal = b[sortConfig.key];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [contactList, filterType, searchTerm, sortConfig]);

  const handleSort = (key: keyof Contact) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      organization: '',
      expertise: '',
      email: '',
      secondary_email: '',
      phone: '',
      notes: '',
      is_internal: false,
    });
    setFormError(null);
  };

  const handleAddContact = () => {
    resetForm();
    setShowAddModal(true);
  };

  const handleEditContact = (contact: Contact) => {
    setFormData({
      name: contact.name,
      organization: contact.organization || '',
      expertise: contact.expertise?.join(', ') || '',
      email: contact.email || '',
      secondary_email: contact.secondary_email || '',
      phone: contact.phone || '',
      notes: contact.notes || '',
      is_internal: contact.is_internal,
    });
    setFormError(null);
    setEditingContact(contact);
    setShowEditModal(true);
  };

  const handleDeleteContact = (contact: Contact) => {
    setDeletingContact(contact);
    setShowDeleteModal(true);
  };

  // Helper to extract validation error message from 422 response
  const extractErrorMessage = (err: unknown): string => {
    if (err && typeof err === 'object' && 'response' in err) {
      const response = (err as { response?: { data?: { detail?: string | Array<{ loc: string[]; msg: string }> } } }).response;
      if (response?.data?.detail) {
        if (typeof response.data.detail === 'string') {
          return response.data.detail;
        }
        if (Array.isArray(response.data.detail)) {
          return response.data.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join(', ');
        }
      }
    }
    return 'An error occurred';
  };

  const submitAdd = async () => {
    setSaving(true);
    setFormError(null);
    try {
      await createContact.mutateAsync({
        name: formData.name,
        organization: formData.organization || null,
        expertise: formData.expertise.split(',').map(e => e.trim()).filter(Boolean),
        email: formData.email,
        secondary_email: formData.secondary_email || null,
        phone: formData.phone || null,
        notes: formData.notes || null,
        is_internal: formData.is_internal,
      });
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const submitEdit = async () => {
    if (!editingContact) return;
    setSaving(true);
    setFormError(null);
    try {
      await updateContact.mutateAsync({
        id: editingContact.id,
        data: {
          name: formData.name,
          organization: formData.organization || null,
          expertise: formData.expertise.split(',').map(e => e.trim()).filter(Boolean),
          email: formData.email,
          secondary_email: formData.secondary_email || null,
          phone: formData.phone || null,
          notes: formData.notes || null,
          is_internal: formData.is_internal,
        },
      });
    } catch (err) {
      setFormError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const submitDelete = async () => {
    if (!deletingContact) return;
    setSaving(true);
    try {
      await deleteContact.mutateAsync(deletingContact.id);
    } finally {
      setSaving(false);
    }
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
          <p>Failed to load contacts</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Contacts</h2>
          <button
            onClick={handleAddContact}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700"
          >
            Add Contact
          </button>
        </div>

        {/* Filters */}
        <div className="mb-6 space-y-4 sm:space-y-0 sm:flex sm:gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or expertise..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div className="sm:w-48">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as 'all' | 'internal' | 'external')}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Contacts</option>
              <option value="internal">Internal</option>
              <option value="external">External</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('name')}
                >
                  <div className="flex items-center">
                    Name
                    {sortConfig.key === 'name' && (
                      <svg
                        className={`ml-2 h-4 w-4 transform ${sortConfig.direction === 'desc' ? 'rotate-180' : ''}`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                    )}
                  </div>
                </th>
                <th
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort('organization')}
                >
                  <div className="flex items-center">
                    Organization
                    {sortConfig.key === 'organization' && (
                      <svg
                        className={`ml-2 h-4 w-4 transform ${sortConfig.direction === 'desc' ? 'rotate-180' : ''}`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                    )}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Expertise
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedContacts.map((contact) => (
                <React.Fragment key={contact.id}>
                  <tr
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => setExpandedId(expandedId === contact.id ? null : contact.id)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {contact.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {contact.organization || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="flex flex-wrap gap-1">
                        {contact.expertise?.slice(0, 3).map(exp => (
                          <span
                            key={exp}
                            className="px-2 py-0.5 text-xs bg-indigo-100 text-indigo-800 rounded-full"
                          >
                            {exp}
                          </span>
                        ))}
                        {contact.expertise && contact.expertise.length > 3 && (
                          <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full">
                            +{contact.expertise.length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" onClick={(e) => e.stopPropagation()}>
                      {contact.email ? (
                        <a
                          href={`mailto:${contact.email}`}
                          className="text-indigo-600 hover:text-indigo-800 hover:underline"
                        >
                          {contact.email}
                        </a>
                      ) : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        contact.is_internal
                          ? 'bg-green-100 text-green-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {contact.is_internal ? 'Internal' : 'External'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex space-x-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => handleEditContact(contact)}
                          className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteContact(contact)}
                          className="text-red-600 hover:text-red-900 text-sm font-medium"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                  {/* Expanded Contact Details Row */}
                  {expandedId === contact.id && (contact.secondary_email || contact.phone || contact.notes) && (
                    <tr className="bg-gray-50">
                      <td colSpan={6} className="px-6 py-4">
                        <div className="flex flex-wrap gap-6 text-sm">
                          {contact.secondary_email && (
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">Secondary:</span>
                              <a
                                href={`mailto:${contact.secondary_email}`}
                                className="text-indigo-600 hover:text-indigo-800 hover:underline"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {contact.secondary_email}
                              </a>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  copyToClipboard(contact.secondary_email!, `secondary-${contact.id}`);
                                }}
                                className="px-2 py-0.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
                              >
                                {copiedField === `secondary-${contact.id}` ? 'Copied!' : 'Copy'}
                              </button>
                            </div>
                          )}
                          {contact.phone && (
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">Phone:</span>
                              <a
                                href={`tel:${contact.phone.replace(/\D/g, '')}`}
                                className="text-gray-900 hover:text-indigo-600"
                                onClick={(e) => e.stopPropagation()}
                              >
                                {formatPhone(contact.phone)}
                              </a>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  copyToClipboard(contact.phone!, `phone-${contact.id}`);
                                }}
                                className="px-2 py-0.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
                              >
                                {copiedField === `phone-${contact.id}` ? 'Copied!' : 'Copy'}
                              </button>
                            </div>
                          )}
                          {contact.notes && (
                            <div className="flex items-start gap-2 w-full">
                              <span className="text-gray-500">Notes:</span>
                              <span className="text-gray-700 flex-1">{contact.notes}</span>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          {filteredAndSortedContacts.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No contacts found matching your criteria.
            </div>
          )}
        </div>
      </div>

      {/* Add Contact Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Add Contact</h3>
            {formError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{formError}</p>
              </div>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Organization</label>
                <input
                  type="text"
                  value={formData.organization}
                  onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Expertise (comma-separated)</label>
                <input
                  type="text"
                  value={formData.expertise}
                  onChange={(e) => setFormData({ ...formData, expertise: e.target.value })}
                  placeholder="mechanical, thermal, electronics"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email <span className="text-red-500">*</span></label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@example.com"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Secondary Email</label>
                <input
                  type="email"
                  value={formData.secondary_email}
                  onChange={(e) => setFormData({ ...formData, secondary_email: e.target.value })}
                  placeholder="alternate@example.com"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+1 (555) 123-4567"
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
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_internal"
                  checked={formData.is_internal}
                  onChange={(e) => setFormData({ ...formData, is_internal: e.target.checked })}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="is_internal" className="ml-2 block text-sm text-gray-700">
                  Internal contact (team member)
                </label>
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
                onClick={submitAdd}
                disabled={saving || !formData.name || !formData.email}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Adding...' : 'Add'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Contact Modal */}
      {showEditModal && editingContact && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Contact</h3>
            {formError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{formError}</p>
              </div>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Organization</label>
                <input
                  type="text"
                  value={formData.organization}
                  onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Expertise (comma-separated)</label>
                <input
                  type="text"
                  value={formData.expertise}
                  onChange={(e) => setFormData({ ...formData, expertise: e.target.value })}
                  placeholder="mechanical, thermal, electronics"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email <span className="text-red-500">*</span></label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="email@example.com"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Secondary Email</label>
                <input
                  type="email"
                  value={formData.secondary_email}
                  onChange={(e) => setFormData({ ...formData, secondary_email: e.target.value })}
                  placeholder="alternate@example.com"
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Phone</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+1 (555) 123-4567"
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
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="edit_is_internal"
                  checked={formData.is_internal}
                  onChange={(e) => setFormData({ ...formData, is_internal: e.target.checked })}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="edit_is_internal" className="ml-2 block text-sm text-gray-700">
                  Internal contact (team member)
                </label>
              </div>
            </div>
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={submitEdit}
                disabled={saving || !formData.name || !formData.email}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Updating...' : 'Update'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingContact && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Delete Contact</h3>
            <p className="text-sm text-gray-500 mb-6">
              Are you sure you want to delete <strong>{deletingContact.name}</strong>?
              This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={saving}
              >
                Cancel
              </button>
              <button
                onClick={submitDelete}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Contacts;
