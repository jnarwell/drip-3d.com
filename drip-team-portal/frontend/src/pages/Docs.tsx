import React from 'react';
import { useLocation } from 'react-router-dom';
import { useDocs } from '../hooks/useDocs';
import DocsSidebar from '../components/docs/DocsSidebar';
import DocsContent from '../components/docs/DocsContent';

const Docs: React.FC = () => {
  const location = useLocation();
  const { content, frontmatter, loading, error } = useDocs(location.pathname);

  return (
    <div className="flex gap-6">
      <DocsSidebar />

      <div className="flex-1 min-w-0">
        {loading && (
          <div className="bg-white shadow rounded-lg p-8">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded w-full"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                <div className="h-4 bg-gray-200 rounded w-4/6"></div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-white shadow rounded-lg p-8">
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                {error === 'Document not found' ? 'Page Not Found' : 'Error Loading Document'}
              </h3>
              <p className="mt-2 text-gray-500">
                {error === 'Document not found'
                  ? "The documentation page you're looking for doesn't exist."
                  : error}
              </p>
            </div>
          </div>
        )}

        {!loading && !error && (
          <DocsContent
            content={content}
            title={frontmatter.title as string | undefined}
          />
        )}
      </div>
    </div>
  );
};

export default Docs;
