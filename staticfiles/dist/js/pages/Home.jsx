import React from 'react';
import { useTranslation } from 'react-i18next';

const Home = () => {
  const { t } = useTranslation();

  return (
    <div className="card mt-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
        {t('home.welcome')}
      </h1>
      <p className="text-lg text-gray-600 dark:text-gray-300">
        {t('home.description')}
      </p>
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card bg-blue-50 dark:bg-blue-900">
          <h3 className="text-xl font-semibold text-blue-900 dark:text-blue-100 mb-2">
            {t('app.description')}
          </h3>
        </div>
      </div>
    </div>
  );
};

export default Home; 