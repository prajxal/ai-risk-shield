import React, { useState, useEffect } from 'react';
import { Send, CheckCircle2, AlertTriangle, XCircle, RotateCcw, Sparkles, ShieldCheck, ArrowRight } from 'lucide-react';

export default function CheckoutSimulator({ onTransactionEvaluated }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('scenario_1_legit');
  const [customPayload, setCustomPayload] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/scenarios')
      .then(res => res.json())
      .then(data => {
        setScenarios(data);
        if (data.length > 0) {
          setSelectedScenarioId(data[0].id);
          setCustomPayload(JSON.stringify(data[0].transaction, null, 2));
        }
      })
      .catch(err => console.error('Failed to load scenarios:', err));
  }, []);

  const handleSelectScenario = (sc) => {
    setSelectedScenarioId(sc.id);
    setCustomPayload(JSON.stringify(sc.transaction, null, 2));
    setResult(null);
    setError(null);
  };

  const handleResetState = async () => {
    try {
      await fetch('/reset', { method: 'POST' });
      alert('Shield sliding window counters reset successfully.');
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const parsedPayload = JSON.parse(customPayload);
      const res = await fetch('/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsedPayload)
      });

      const data = await res.json();
      if (res.status === 403) {
        // BLOCKED
        setResult({
          status: 'BLOCKED',
          statusCode: 403,
          action: 'BLOCK',
          ...data.detail
        });
      } else if (res.ok) {
        // ALLOW or FLAG
        setResult({
          statusCode: 200,
          action: data.decision?.action || 'ALLOW',
          ...data
        });
      } else {
        setError(data.detail || 'Evaluation failed');
      }

      if (onTransactionEvaluated) {
        onTransactionEvaluated();
      }
    } catch (err) {
      setError(`Request error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="simulator-container">
      {/* Scenario Picker */}
      <div className="card">
        <div className="card-title">
          <Sparkles size={18} color="#3395ff" />
          <span>Pitch Demo Scenarios (One-Click Selection)</span>
        </div>
        <p className="card-desc">
          Select a preset AI-agent transaction scenario from the 5-minute pitch or edit the JSON payload below.
        </p>

        <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          {scenarios.map((sc) => (
            <div
              key={sc.id}
              className={`scenario-card ${selectedScenarioId === sc.id ? 'selected' : ''}`}
              onClick={() => handleSelectScenario(sc)}
            >
              <div className="scenario-card-header">
                <span className="scenario-card-title">{sc.name}</span>
                <span className={`badge badge-${sc.badge_type}`}>{sc.badge}</span>
              </div>
              <p className="scenario-card-desc">{sc.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Editor and Results Grid */}
      <div className="grid-2">
        {/* Left Column: JSON Payload Editor */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-title" style={{ justifyContent: 'space-between' }}>
            <span>Transaction Payload (POST /checkout)</span>
            <button className="btn-secondary" onClick={handleResetState} title="Reset rate limit counters">
              <RotateCcw size={14} />
              Reset State
            </button>
          </div>
          <p className="card-desc">
            Standard <code>Transaction</code> contract submitted by autonomous buyer agent.
          </p>

          <textarea
            className="code-block font-mono"
            style={{
              width: '100%',
              minHeight: '340px',
              flex: 1,
              resize: 'vertical',
              color: '#a5f3fc',
              outline: 'none',
              lineHeight: 1.4,
              fontSize: '0.8rem'
            }}
            value={customPayload}
            onChange={(e) => setCustomPayload(e.target.value)}
          />

          <div style={{ marginTop: '1.25rem', display: 'flex', gap: '1rem' }}>
            <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
              <Send size={16} />
              {loading ? 'Evaluating in Shield Proxy...' : 'Submit to Shield Defensive Proxy'}
            </button>
          </div>
        </div>

        {/* Right Column: Live Decision Outcome */}
        <div className="card">
          <div className="card-title">
            <ShieldCheck size={18} color="#10b981" />
            <span>Shield Defensive Decision & Audit Verdict</span>
          </div>
          <p className="card-desc">
            Real-time inline proxy evaluation results, risk scoring, and policy reasoning.
          </p>

          {loading && (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <div className="status-dot" style={{ width: 14, height: 14, margin: '0 auto 1rem', background: '#3395ff' }}></div>
              <p>Executing Sequential Checks: Injection → Intent-Consistency → Velocity...</p>
            </div>
          )}

          {error && (
            <div style={{ padding: '1.5rem', background: 'var(--color-block-bg)', border: '1px solid var(--color-block-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-block)' }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          {!loading && !result && !error && (
            <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-dim)' }}>
              <Send size={36} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
              <p>Click "Submit to Shield Defensive Proxy" to inspect the transaction.</p>
            </div>
          )}

          {!loading && result && (
            <div className="decision-result-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Verdict Header */}
              <div style={{
                padding: '1.25rem',
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: result.action === 'ALLOW' ? 'var(--color-allow-bg)' : (result.action === 'FLAG' ? 'var(--color-flag-bg)' : 'var(--color-block-bg)'),
                border: `1px solid ${result.action === 'ALLOW' ? 'var(--color-allow-border)' : (result.action === 'FLAG' ? 'var(--color-flag-border)' : 'var(--color-block-border)')}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  {result.action === 'ALLOW' && <CheckCircle2 size={32} color="var(--color-allow)" />}
                  {result.action === 'FLAG' && <AlertTriangle size={32} color="var(--color-flag)" />}
                  {result.action === 'BLOCK' && <XCircle size={32} color="var(--color-block)" />}
                  <div>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                      {result.action === 'ALLOW' && '✅ 200 OK — ALLOWED (Payment Processed)'}
                      {result.action === 'FLAG' && '⚠️ 200 OK — FLAGGED (Merchant Review)'}
                      {result.action === 'BLOCK' && '🛑 403 Forbidden — BLOCKED (Threat Intercepted)'}
                    </h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Transaction ID: <span className="font-mono">{result.transaction_id}</span>
                    </p>
                  </div>
                </div>
                <span className={`badge badge-${result.action === 'ALLOW' ? 'success' : (result.action === 'FLAG' ? 'warning' : 'danger')}`} style={{ fontSize: '0.85rem', padding: '0.4rem 0.85rem' }}>
                  {result.action}
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid-3">
                <div className="stat-box">
                  <span className="stat-label">Assigned Risk Score</span>
                  <span className="stat-value" style={{
                    color: (result.decision?.risk_score ?? result.risk_score) > 60 ? 'var(--color-block)' : ((result.decision?.risk_score ?? result.risk_score) > 20 ? 'var(--color-flag)' : 'var(--color-allow)')
                  }}>
                    {result.decision?.risk_score ?? result.risk_score ?? 0}
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}> / 100</span>
                  </span>
                </div>

                <div className="stat-box">
                  <span className="stat-label">Model Confidence</span>
                  <span className="stat-value" style={{ color: '#fff' }}>
                    {((result.decision?.confidence ?? result.confidence ?? 1.0) * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="stat-box">
                  <span className="stat-label">Audit Log Ref</span>
                  <span className="stat-value font-mono" style={{ fontSize: '1.1rem', color: 'var(--rzp-blue)' }}>
                    {result.audit_id || 'N/A'}
                  </span>
                </div>
              </div>

              {/* Triggered Checks */}
              <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Triggered Threat Checks:
                </span>
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                  {(result.decision?.triggered_checks || result.triggered_checks || []).length > 0 ? (
                    (result.decision?.triggered_checks || result.triggered_checks).map(chk => (
                      <span key={chk} className="badge badge-danger font-mono" style={{ textTransform: 'none' }}>
                        {chk}
                      </span>
                    ))
                  ) : (
                    <span className="badge badge-success font-mono" style={{ textTransform: 'none' }}>
                      None (All Defensive Checks Passed)
                    </span>
                  )}
                </div>
              </div>

              {/* Policy Rationale */}
              <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Auditable Policy Rationale:
                </span>
                <p style={{ marginTop: '0.35rem', fontSize: '0.9rem', color: '#fff', lineHeight: 1.5 }}>
                  {result.decision?.reason || result.reason || result.message}
                </p>
              </div>

              {result.payment_id && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Mock Payment Token: <code className="font-mono" style={{ color: 'var(--color-allow)' }}>{result.payment_id}</code> (Amount: ₹{result.amount_charged})
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
