import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  DocumentTextIcon,
  TableCellsIcon,
  ChartBarIcon,
  BookmarkIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';

export default function Layout() {
  const location = useLocation();

  const navigation = [
    { name: '首页', href: '/', icon: HomeIcon },
    { name: '财报查询', href: '/reports', icon: DocumentTextIcon },
    { name: '科目查询', href: '/accounts', icon: TableCellsIcon },
    { name: '财报分析', href: '/analysis', icon: ChartBarIcon },
    { name: '笔记附注', href: '/notes', icon: BookmarkIcon },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <h1 className="text-2xl font-bold text-primary-600">OmniExtract-VL</h1>
              </Link>
            </div>

            {/* Navigation */}
            <div className="hidden md:flex space-x-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive(item.href)
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <item.icon className="h-5 w-5 mr-2" />
                  {item.name}
                </Link>
              ))}
            </div>

            {/* User menu */}
            <div className="flex items-center">
              <Link
                to="/login"
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <UserCircleIcon className="h-8 w-8" />
              </Link>
            </div>
          </div>
        </div>

        {/* Mobile navigation */}
        <div className="md:hidden border-t border-gray-200">
          <div className="flex justify-around py-2">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`flex flex-col items-center px-3 py-2 text-xs font-medium transition-colors ${
                  isActive(item.href)
                    ? 'text-primary-700'
                    : 'text-gray-600'
                }`}
              >
                <item.icon className="h-6 w-6 mb-1" />
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            © 2026 OCR Agent Platform
          </p>
        </div>
      </footer>
    </div>
  );
}
