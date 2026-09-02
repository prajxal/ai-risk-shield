import React, { useState, useEffect } from 'react';
import { Shield, Activity, Terminal, FileText, BarChart3, AlertCircle, Zap, Radio, Gauge } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, apiStatus }) {
  const [streamStatus, setStreamStatus] = useState({
    is_running: false,
    interval_ms: 2000,
    attack_ratio: 0.4,
    total_generated_count: 0,
    allowed_count: 0,
    flagged_count: 0,
    blocked_count: 0,
    last_event_id: null,
    last_decision: null
  });
  const [loading, setLoading] = useState(false);

  const fetchStreamStatus = async () => {
    try {
      const res = await fetch('/stream/status');
      if (res.ok) {
        const data = await res.json();
        setStreamStatus(data);
      }
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchStreamStatus();
    const interval = setInterval(fetchStreamStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleToggle = async () => {
    setLoading(true);
    try {
      if (streamStatus.is_running) {
        const res = await fetch('/stream/stop', { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          setStreamStatus(data);
        }
      } else {
        const res = await fetch('/stream/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ interval_ms: streamStatus.interval_ms, attack_ratio: streamStatus.attack_ratio })
        });
        if (res.ok) {
          const data = await res.json();
          setStreamStatus(data);
        }
      }
    } catch (e) {
      console.error('Failed to toggle live stream:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeedChange = async (intervalMs) => {
    try {
      const res = await fetch('/stream/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interval_ms: intervalMs })
      });
      if (res.ok) {
        const data = await res.json();
        setStreamStatus(data);
      }
    } catch (e) {
      console.error('Failed to change speed:', e);
    }
  };

  const currentSpeed =
    streamStatus.interval_ms <= 300 ? '5x' :
    streamStatus.interval_ms <= 1000 ? '3x' : '1x';

  return (
    <header className="app-header">
      <div className="header-top">
        <div className="logo-section">
          <div className="logo-badge">
            <Shield size={24} />
          </div>
          <div className="logo-text">
            <h1>Razorpay Return-Risk Shield</h1>
            <span className="subtitle">Track 02: AI Risk Manager • Merchant Loss & Return Abuse Defense</span>
          </div>
        </div>

        <div className="header-meta">
          {/* Live Traffic Control Center */}
          <div className={`live-traffic-control ${streamStatus.is_running ? 'active' : ''}`}>
            <div className="live-toggle-wrapper">
              <span className="live-toggle-label">
                <Radio size={14} className={streamStatus.is_running ? 'pulse-icon' : ''} />
                Live Returns:
              </span>
              <button
                type="button"
                className={`toggle-switch-btn ${streamStatus.is_running ? 'on' : 'off'}`}
                onClick={handleToggle}
                disabled={loading || !apiStatus}
                title={streamStatus.is_running ? 'Click to Stop Live Returns' : 'Click to Start Live Returns'}
              >
                <span className="toggle-indicator"></span>
                <span className="toggle-text">{streamStatus.is_running ? 'ON' : 'OFF'}</span>
              </button>
            </div>

            {/* Speed Presets */}
            <div className="speed-presets-wrapper">
              <span className="speed-label">
                <Gauge size={13} />
                Speed:
              </span>
              <div className="speed-btn-group">
                <button
                  type="button"
                  className={`speed-pill-btn ${currentSpeed === '1x' ? 'selected' : ''}`}
                  onClick={() => handleSpeedChange(2000)}
                  title="1x Normal Speed (~2000ms/event)"
                >
                  1x Normal
                </button>
                <button
                  type="button"
                  className={`speed-pill-btn ${currentSpeed === '3x' ? 'selected' : ''}`}
                  onClick={() => handleSpeedChange(750)}
                  title="3x Fast Speed (~750ms/event)"
                >
                  3x Fast
                </button>
                <button
                  type="button"
                  className={`speed-pill-btn ${currentSpeed === '5x' ? 'selected' : ''}`}
                  onClick={() => handleSpeedChange(250)}
                  title="5x Turbo Speed (~250ms/event, sampled disk writes)"
                >
                  5x Turbo
                </button>
              </div>
            </div>

            {/* Live Counter Badge */}
            {streamStatus.is_running && (
              <div className="live-stream-counter">
                <Zap size={13} color="#10b981" />
                <span>{streamStatus.total_generated_count} events</span>
              </div>
            )}
          </div>

          <span className="pill-disclosure">
            ⚠️ Test-Mode Simulation & Synthetic Evaluation
          </span>
          <div className={`status-pill ${apiStatus ? 'online' : 'offline'}`}>
            <span className="status-dot"></span>
            <span>{apiStatus ? 'Shield Proxy Active' : 'Connecting to Shield...'}</span>
          </div>
        </div>
      </div>

      <nav className="nav-tabs-container">
        <button
          className={`nav-tab-btn ${activeTab === 'simulator' ? 'active' : ''}`}
          onClick={() => setActiveTab('simulator')}
        >
          <Terminal size={16} />
          Return Risk Simulator
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
