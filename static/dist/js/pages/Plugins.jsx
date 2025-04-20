import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

const Plugins = () => {
  const { t } = useTranslation();
  const [plugins, setPlugins] = useState([
    {
      id: 1,
      name: 'Example Plugin',
      description: 'An example plugin that demonstrates the plugin system',
      enabled: true,
      version: '1.0.0'
    }
    // Add more plugins here
  ]);

  const togglePlugin = (id) => {
    setPlugins(plugins.map(plugin =>
      plugin.id === id ? { ...plugin, enabled: !plugin.enabled } : plugin
    ));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {t('plugins.title')}
        </h1>
        <button className="btn-primary">
          + {t('plugins.actions.add')}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plugins.map(plugin => (
          <div key={plugin.id} className="card">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {plugin.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  v{plugin.version}
                </p>
              </div>
              <div className="flex items-center">
                <span className={`px-2 py-1 text-xs rounded-full ${
                  plugin.enabled
                    ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                }`}>
                  {plugin.enabled ? t('plugins.enabled') : t('plugins.disabled')}
                </span>
              </div>
            </div>

            <p className="text-gray-600 dark:text-gray-300 mb-4">
              {plugin.description}
            </p>

            <div className="flex space-x-2">
              <button
                onClick={() => togglePlugin(plugin.id)}
                className={`btn ${
                  plugin.enabled ? 'btn-secondary' : 'btn-primary'
                }`}
              >
                {plugin.enabled
                  ? t('plugins.actions.disable')
                  : t('plugins.actions.enable')}
              </button>
              <button className="btn-secondary">
                {t('plugins.actions.configure')}
              </button>
              <button className="btn-secondary text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300">
                {t('plugins.actions.delete')}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Plugins; 