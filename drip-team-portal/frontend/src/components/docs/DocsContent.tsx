import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSlug from 'rehype-slug';
import { Link } from 'react-router-dom';
import type { Components } from 'react-markdown';

interface DocsContentProps {
  content: string;
  title?: string;
}

const DocsContent: React.FC<DocsContentProps> = ({ content, title }) => {
  // Custom components for react-markdown
  const components: Components = {
    // Handle internal links with React Router
    a: ({ href, children, ...props }) => {
      // Check if internal link
      if (href && (href.startsWith('/docs') || href.startsWith('./') || href.startsWith('../'))) {
        // Normalize relative paths
        let normalizedHref = href;
        if (href.startsWith('./') || href.startsWith('../')) {
          // For now, treat as relative to /docs
          normalizedHref = `/docs/${href.replace(/^\.\//, '').replace(/\.md$/, '')}`;
        }
        // Remove .md extension if present
        normalizedHref = normalizedHref.replace(/\.md$/, '');

        return (
          <Link to={normalizedHref} className="text-indigo-600 hover:text-indigo-800 underline">
            {children}
          </Link>
        );
      }
      // External links
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-600 hover:text-indigo-800 underline"
          {...props}
        >
          {children}
        </a>
      );
    },
    // Custom code block styling
    code: ({ className, children, ...props }) => {
      const match = /language-(\w+)/.exec(className || '');
      const isInline = !match && !className;

      if (isInline) {
        return (
          <code
            className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono"
            {...props}
          >
            {children}
          </code>
        );
      }

      return (
        <code className={`block ${className || ''}`} {...props}>
          {children}
        </code>
      );
    },
    // Wrap pre for better code block styling
    pre: ({ children, ...props }) => (
      <pre
        className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono"
        {...props}
      >
        {children}
      </pre>
    ),
    // Table styling
    table: ({ children, ...props }) => (
      <div className="overflow-x-auto my-4">
        <table className="min-w-full divide-y divide-gray-200 border" {...props}>
          {children}
        </table>
      </div>
    ),
    thead: ({ children, ...props }) => (
      <thead className="bg-gray-50" {...props}>
        {children}
      </thead>
    ),
    th: ({ children, ...props }) => (
      <th
        className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b"
        {...props}
      >
        {children}
      </th>
    ),
    td: ({ children, ...props }) => (
      <td className="px-4 py-3 text-sm text-gray-700 border-b" {...props}>
        {children}
      </td>
    ),
  };

  return (
    <div className="bg-white shadow rounded-lg p-8">
      {title && (
        <h1 className="text-3xl font-bold text-gray-900 mb-6 pb-4 border-b">
          {title}
        </h1>
      )}
      <article className="prose prose-indigo max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSlug]}
          components={components}
        >
          {content}
        </ReactMarkdown>
      </article>
    </div>
  );
};

export default DocsContent;
