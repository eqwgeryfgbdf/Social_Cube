import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const Navbar = () => {
  const { t } = useTranslation();

  return (
    <nav className="bg-white dark:bg-gray-800 shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center justify-between w-full">
            <div className="flex-shrink-0 flex items-center">
              <Link to="/" className="text-xl font-bold text-gray-800 dark:text-white">
                {t('app.title')}
              </Link>
            </div>
            <div className="flex space-x-4">
              <Link
                to="/"
                className="nav-link"
              >
                {t('nav.home')}
              </Link>
              <Link
                to="/plugins"
                className="nav-link"
              >
                {t('nav.plugins')}
              </Link>
              <Link
                to="/settings"
                className="nav-link"
              >
                {t('nav.settings')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 