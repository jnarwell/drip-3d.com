import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import type { TestProtocol } from '../../types';

const CATEGORY_COLORS: Record<string, string> = {
  Acoustic: 'bg-purple-100 text-purple-800',
  Thermal: 'bg-orange-100 text-orange-800',
  Mechanical: 'bg-blue-100 text-blue-800',
  Electrical: 'bg-yellow-100 text-yellow-800',
  Integration: 'bg-green-100 text-green-800',
  System: 'bg-cyan-100 text-cyan-800',
  'Physics Validation': 'bg-pink-100 text-pink-800',
};

const ProtocolList: React.FC = () => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  // Filter state
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string>('');
  const [showInactive, setShowInactive] = useState(false);

  // Fetch protocols
  const { data: protocols, isLoading, error } = useQuery<TestProtocol[]>({
    queryKey: ['test-protocols', { category, search, showInactive }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      if (search) params.append('search', search);
      if (!showInactive) params.append('is_active', 'true');
      const response = await api.get(`/api/v1/test-protocols?${params}`);
      return response.data;
    },
  });

  // Fetch categories for filter dropdown
  const { data: categories } = useQuery<string[]>({
    queryKey: ['test-protocol-categories'],
    queryFn: async () => {
      const response = await api.get('/api/v1/test-protocols/categories');
      return response.data;
    },
  });

  // Delete mutation (soft delete)
  const deleteProtocol = useMutation({
    mutationFn: async (protocolId: number) => {
      await api.delete(`/api/v1/test-protocols/${protocolId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test-protocols'] });
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to delete protocol');
    },
  });

  const handleDelete = (protocol: TestProtocol) => {
    if (window.confirm(`Deactivate "${protocol.name}"? This will hide it from the list.`)) {
      deleteProtocol.mutate(protocol.id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading protocols</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Test Protocols</h1>
          <p className="mt-1 text-sm text-gray-500">
            Reusable test templates with defined inputs, outputs, and procedures.
          </p>
        </div>
        <Link
          to="/testing/protocols/new"
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Protocol
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search protocols..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          {/* Category dropdown */}
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="">All Categories</option>
            {categories?.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Show inactive toggle */}
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            Show inactive
          </label>
        </div>
      </div>

      {/* Protocol Grid */}
      {protocols?.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No protocols</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating a new test protocol.</p>
          <div className="mt-6">
            <Link
              to="/testing/protocols/new"
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
            >
              Create Protocol
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {protocols?.map((protocol) => (
            <div
              key={protocol.id}
              className={`bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow ${
                !protocol.is_active ? 'opacity-60' : ''
              }`}
            >
              <div className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <Link
                      to={`/testing/protocols/${protocol.id}`}
                      className="text-lg font-semibold text-gray-900 hover:text-indigo-600 truncate block"
                    >
                      {protocol.name}
                    </Link>
                    {protocol.description && (
                      <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                        {protocol.description}
                      </p>
                    )}
                  </div>
                  {!protocol.is_active && (
                    <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                      Inactive
                    </span>
                  )}
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {protocol.category && (
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                      CATEGORY_COLORS[protocol.category] || 'bg-gray-100 text-gray-800'
                    }`}>
                      {protocol.category}
                    </span>
                  )}
                  <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                    v{protocol.version}
                  </span>
                  <span className="px-2 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-700 rounded">
                    {protocol.run_count || 0} runs
                  </span>
                </div>

                {/* Schema summary */}
                <div className="flex gap-4 text-xs text-gray-500 mb-4">
                  <span>
                    {protocol.input_schema?.length || 0} inputs
                  </span>
                  <span>
                    {protocol.output_schema?.length || 0} outputs
                  </span>
                  {protocol.equipment?.length ? (
                    <span>{protocol.equipment.length} equipment</span>
                  ) : null}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-3 border-t">
                  <Link
                    to={`/testing/protocols/${protocol.id}`}
                    className="flex-1 text-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
                  >
                    View
                  </Link>
                  <Link
                    to={`/testing/protocols/${protocol.id}/run`}
                    className="flex-1 text-center px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700"
                  >
                    Run Test
                  </Link>
                  <button
                    onClick={() => handleDelete(protocol)}
                    className="px-3 py-1.5 text-sm font-medium text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                    title="Deactivate"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProtocolList;
