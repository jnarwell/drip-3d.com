import React from 'react';
import { PropertyTableSummary, VerificationStatus } from '../../types/resources';
import { formatDistanceToNow } from 'date-fns';

interface PropertyTablesListProps {
  tables: PropertyTableSummary[];
}

const PropertyTablesList: React.FC<PropertyTablesListProps> = ({ tables }) => {
  const getVerificationBadge = (status: VerificationStatus) => {
    switch (status) {
      case VerificationStatus.VERIFIED:
        return <span className="text-green-600">🟢</span>;
      case VerificationStatus.CITED:
        return <span className="text-yellow-600">🟡</span>;
      case VerificationStatus.UNVERIFIED:
        return <span className="text-red-600">🔴</span>;
    }
  };

  const getImportMethodLabel = (method: string) => {
    switch (method) {
      case 'document_import':
        return 'Document';
      case 'api_import':
        return 'API';
      case 'manual_entry':
        return 'Manual';
      case 'copied':
        return 'Copied';
      default:
        return method;
    }
  };

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Table Name
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Material
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Data Points
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Import Method
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Source
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Updated
              </th>
              <th scope="col" className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tables.map((table) => (
              <tr key={table.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      {getVerificationBadge(table.verification_status)}
                    </div>
                    <div className="ml-3">
                      <div className="text-sm font-medium text-gray-900">
                        {table.name}
                      </div>
                      {table.description && (
                        <div className="text-sm text-gray-500 max-w-xs truncate">
                          {table.description}
                        </div>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{table.material_name || '—'}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{table.data_points_count}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                    {getImportMethodLabel(table.import_method)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm">
                    {table.source_authority ? (
                      <div>
                        <div className="text-gray-900 font-medium">{table.source_authority}</div>
                        {table.source_citation && (
                          <div className="text-gray-500 text-xs truncate max-w-xs" title={table.source_citation}>
                            {table.source_citation}
                          </div>
                        )}
                      </div>
                    ) : table.source_citation ? (
                      <div className="text-gray-500 text-xs truncate max-w-xs" title={table.source_citation}>
                        {table.source_citation}
                      </div>
                    ) : (
                      <span className="text-gray-400">No source</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDistanceToNow(new Date(table.last_updated), { addSuffix: true })}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button className="text-indigo-600 hover:text-indigo-900 mr-3">
                    View
                  </button>
                  <button className="text-gray-600 hover:text-gray-900">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PropertyTablesList;