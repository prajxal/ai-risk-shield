import React from 'react';
import { Shield, Activity, Terminal, FileText, BarChart3, AlertCircle } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, apiStatus }) {
  return (
    <header className="app-header">
      <div className="header-top">
        <div className="logo-section">
          <div className="logo-badge">
            <Shield size={24} />
          </div>
          <div className="logo-text">
            <h1>Razorpay AI Risk Shield</h1>
            <span className="subtitle">Track 02: AI Risk Manager • Autonomous Agentic Commerce Defense</span>
          </div>
        </div>

        <div className="header-meta">
          <span className="pill-disclosure">
            ⚠️ Test-Mode Simulation & Synthetic Evaluation
          </span>
          <div className={`status-pill ${apiStatus ? 'online' : 'offline'}`}>
            <span className="status-dot"></span>
            <span>{apiStatus ? 'Shield Proxy Active (Port 8000)' : 'Connecting to Shield...'}</span>
          </div>
        </div>
      </div>

      <nav className="nav-tabs-container">
        <button
          className={`nav-tab-btn ${activeTab === 'simulator' ? 'active' : ''}`}
          onClick={() => setActiveTab('simulator')}
        >
          <Terminal size={16} />
          Live Checkout Simulator
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          <FileText size={16} />
          Structured Audit Trail
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
          onClick={() => setActiveTab('benchmark')}
        >
          <BarChart3 size={16} />
          Benchmark Evaluation (Held-Out)
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'failure' ? 'active' : ''}`}
          onClick={() => setActiveTab('failure')}
        >
          <AlertCircle size={16} />
          Honest-Failure Spotlight
        </button>
      </nav>
    </header>
  );
}
