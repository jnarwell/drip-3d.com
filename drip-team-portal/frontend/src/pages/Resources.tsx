import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';

const Resources: React.FC = () => {
  const location = useLocation();
  
  const navigation = [
    { name: 'Data Tables', href: '/resources/property-tables' },
    { name: 'Constants', href: '/resources/constants' },
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className="flex gap-6">
      {/* Left Sidebar Navigation */}
      <nav className="w-64 flex-shrink-0">
        <div className="bg-white shadow rounded-lg p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Resources</h2>
          <ul className="space-y-1">
            {navigation.map((item) => (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={`block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive(item.href)
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="flex-1">
        <Outlet />
      </div>
    </div>
  );
};

export default Resources;