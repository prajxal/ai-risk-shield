import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import CheckoutSimulator from './components/CheckoutSimulator';
import AuditTrail from './components/AuditTrail';
import BenchmarkDashboard from './components/BenchmarkDashboard';
import HonestFailureSpotlight from './components/HonestFailureSpotlight';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('simulator');
  const [apiOnline, setApiOnline] = useState(false);
  const [auditRefreshKey, setAuditRefreshKey] = useState(0);

  const checkHealth = async () => {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        setApiOnline(true);
      } else {
        setApiOnline(false);
      }
    } catch (e) {
      setApiOnline(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleTransactionEvaluated = () => {
    setAuditRefreshKey(prev => prev + 1);
  };

  return (
    <div className="app-container">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        apiStatus={apiOnline}
      />

      <main className="main-content">
        {activeTab === 'simulator' && (
          <CheckoutSimulator onTransactionEvaluated={handleTransactionEvaluated} />
        )}
        {activeTab === 'audit' && (
          <AuditTrail
            refreshTrigger={auditRefreshKey}
            onNavigateToSimulator={() => setActiveTab('simulator')}
          />
        )}
        {activeTab === 'benchmark' && (
          <BenchmarkDashboard />
        )}
        {activeTab === 'failure' && (
          <HonestFailureSpotlight />
        )}
      </main>
    </div>
  );
}
