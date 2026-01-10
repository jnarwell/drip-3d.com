import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { docsNav, DocNavSection, DocNavItem } from '../../config/docsNav';

interface NavItemProps {
  item: DocNavItem;
  isActive: boolean;
  depth?: number;
}

const NavItem: React.FC<NavItemProps> = ({ item, isActive, depth = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = item.children && item.children.length > 0;
  const location = useLocation();

  const checkIsActive = (path: string) => location.pathname === path;

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors ${
            depth > 0 ? 'pl-6' : ''
          }`}
        >
          <span>{item.title}</span>
          <svg
            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        {isExpanded && (
          <div className="ml-3">
            {item.children!.map((child) => (
              <NavItem
                key={child.path || child.title}
                item={child}
                isActive={child.path ? checkIsActive(child.path) : false}
                depth={depth + 1}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  if (!item.path) return null;

  return (
    <Link
      to={item.path}
      className={`block px-3 py-2 text-sm font-medium rounded-md transition-colors ${
        depth > 0 ? 'pl-6' : ''
      } ${
        isActive
          ? 'bg-indigo-100 text-indigo-700'
          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
      }`}
    >
      {item.title}
    </Link>
  );
};

interface NavSectionProps {
  section: DocNavSection;
}

const NavSection: React.FC<NavSectionProps> = ({ section }) => {
  const location = useLocation();
  const checkIsActive = (path: string) => location.pathname === path;

  return (
    <div className="mb-6">
      <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        {section.title}
      </h3>
      <ul className="space-y-1">
        {section.items.map((item) => (
          <li key={item.path || item.title}>
            <NavItem
              item={item}
              isActive={item.path ? checkIsActive(item.path) : false}
            />
          </li>
        ))}
      </ul>
    </div>
  );
};

const DocsSidebar: React.FC = () => {
  return (
    <nav className="w-64 flex-shrink-0">
      <div className="sticky top-4 bg-white shadow rounded-lg p-4 max-h-[calc(100vh-2rem)] overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Documentation</h2>
        {docsNav.map((section) => (
          <NavSection key={section.title} section={section} />
        ))}
      </div>
    </nav>
  );
};

export default DocsSidebar;
