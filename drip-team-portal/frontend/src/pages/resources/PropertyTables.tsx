import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import CreatePropertyTableModal from '../../components/resources/CreatePropertyTableModal';
import PropertyTablesList from '../../components/resources/PropertyTablesList';
import { PropertyTableSummary, VerificationStatus } from '../../types/resources';

const PropertyTables: React.FC = () => {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<VerificationStatus | 'all'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch property tables
  const { data: tables, isLoading, error } = useQuery<PropertyTableSummary[]>({
    queryKey: ['property-tables', selectedFilter, searchTerm],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedFilter !== 'all') {
        params.append('verification_status', selectedFilter);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      const response = await api.get(`/api/v1/enhanced/property-tables?${params}`);
      return response.data;
    }
  });

  const hasAnyTables = tables && tables.length > 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="sm:flex sm:items-center sm:justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Property Tables</h2>
            <p className="mt-1 text-sm text-gray-600">
              Import and manage property lookup tables for materials and calculations
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsCreateModalOpen(true)}
            className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <svg className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Table
          </button>
        </div>

        {hasAnyTables && (
          <>
            {/* Filters */}
            <div className="mb-4 space-y-4 sm:space-y-0 sm:flex sm:gap-4">
              <div className="flex-1">
                <label htmlFor="search" className="sr-only">
                  Search tables
                </label>
                <input
                  type="text"
                  id="search"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search by name, description, or source..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <div className="sm:w-48">
                <label htmlFor="filter" className="sr-only">
                  Filter by status
                </label>
                <select
                  id="filter"
                  value={selectedFilter}
                  onChange={(e) => setSelectedFilter(e.target.value as VerificationStatus | 'all')}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="all">All Tables</option>
                  <option value="verified">🟢 Verified Only</option>
                  <option value="cited">🟡 Cited Only</option>
                  <option value="unverified">🔴 Unverified Only</option>
                </select>
              </div>
            </div>

            {/* Verification Legend */}
            <div className="bg-gray-50 rounded-md p-3 text-xs">
              <div className="flex flex-wrap gap-4">
                <span className="flex items-center">
                  <span className="text-green-600 mr-1">🟢</span>
                  <span className="font-medium">Verified:</span>
                  <span className="ml-1 text-gray-600">Imported from authoritative source</span>
                </span>
                <span className="flex items-center">
                  <span className="text-yellow-600 mr-1">🟡</span>
                  <span className="font-medium">Cited:</span>
                  <span className="ml-1 text-gray-600">Manual entry with source</span>
                </span>
                <span className="flex items-center">
                  <span className="text-red-600 mr-1">🔴</span>
                  <span className="font-medium">Unverified:</span>
                  <span className="ml-1 text-gray-600">No source documentation</span>
                </span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Table List or Empty State */}
      {isLoading ? (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      ) : error ? (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="text-red-600">
            <h3 className="text-lg font-semibold mb-2">Error</h3>
            <p>Failed to load property tables</p>
          </div>
        </div>
      ) : hasAnyTables ? (
        <PropertyTablesList tables={tables} />
      ) : (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No property tables yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Get started by creating your first property table.
            </p>
            <div className="mt-6">
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create your first table
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Table Modal */}
      {isCreateModalOpen && (
        <CreatePropertyTableModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
        />
      )}
    </div>
  );
};

export default PropertyTables;