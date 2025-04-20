import React from 'react';
import { I18nextProvider } from 'react-i18next';
import i18n from './i18n';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Plugins from './pages/Plugins';
import Settings from './pages/Settings';
import { Routes, Route } from 'react-router-dom';

function App() {
  return (
    <I18nextProvider i18n={i18n}>
      <div className="app">
        <nav className="navbar">
          <div className="navbar-brand">Social Cube</div>
          <div className="navbar-menu">
            <a href="#" className="navbar-item">首页</a>
            <a href="#" className="navbar-item">插件</a>
            <a href="#" className="navbar-item">设置</a>
          </div>
        </nav>
        
        <main className="main-content">
          <h1>欢迎使用 Social Cube</h1>
          <p>强大的社交媒体管理平台</p>
          <div className="feature-card">
            <h2>Discord 机器人管理平台</h2>
          </div>
        </main>
      </div>
    </I18nextProvider>
  );
}

export default App; 