import React, { useState, useEffect } from 'react';
import { Play, ShieldAlert, CheckCircle2, AlertTriangle, XCircle, RefreshCw, Send, Terminal, Layers } from 'lucide-react';

export default function OrderSimulator({ onEvaluationSuccess }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState('');
  const [payloadText, setPayloadText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Fetch scenarios on mount
  useEffect(() => {
    fetch('/scenarios')
      .then(res => res.json())
      .then(data => {
        setScenarios(data);
        if (data && data.length > 0) {
          loadScenario(data[0]);
        }
      })
      .catch(err => console.error('Failed to load scenarios:', err));
  }, []);

  const loadScenario = (scenario) => {
    setSelectedScenarioId(scenario.id);
    const eventObj = scenario.return_event || scenario.transaction;
    setPayloadText(JSON.stringify(eventObj, null, 2));
    setResult(null);
    setError(null);
  };

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let parsedPayload;
      try {
        parsedPayload = JSON.parse(payloadText);
      } catch (e) {
        throw new Error(`JSON Syntax Error: ${e.message}`);
      }

      const res = await fetch('/returns/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parsedPayload)
      });

      const data = await res.json();

      if (!res.ok) {
        // Handled 403 Forbidden or 422 Unprocessable Entity
        if (res.status === 403 && data.detail) {
          setResult({
            status: 'BLOCKED',
            isBlocked: true,
            detail: data.detail
          });
        } else {
          setError(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
        }
      } else {
        setResult({
          status: data.status,
          isBlocked: false,
          data: data
        });
      }

      if (onEvaluationSuccess) {
        onEvaluationSuccess();
      }
    } catch (err) {
      setError(err.message || 'Failed to communicate with Shield Proxy.');
    } finally {
      setLoading(false);
    }
  };

  const decisionObj = result?.data?.decision || result?.detail;
  const riskScore = decisionObj?.risk_score ?? 0;
  const actionStr = decisionObj?.action || result?.status || 'UNKNOWN';

  return (
    <div className="simulator-container">
      {/* Scenario Presets Bar */}
      <div className="card">
        <div className="card-title" style={{ marginBottom: '0.75rem' }}>
          <Layers size={18} color="#3395ff" />
          <span>Preset Return-Risk Scenarios</span>
        </div>
        <p className="card-desc">
          Select an interactive demo preset to evaluate how the Return-Risk Shield classifies legitimate vs abusive return behaviors.
        </p>

        <div className="scenario-grid">
          {scenarios.map((sc) => {
            const isSelected = selectedScenarioId === sc.id;
            return (
              <button
                key={sc.id}
                className={`scenario-btn ${isSelected ? 'active' : ''}`}
                onClick={() => loadScenario(sc)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{sc.name}</span>
                  <span className={`badge badge-${sc.badge_type || 'info'}`}>{sc.badge}</span>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textAlign: 'left', margin: 0 }}>
                  {sc.description}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Execution Workspace */}
      <div className="grid-2">
        {/* Left Column: Return Event JSON Payload Editor */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <div className="card-title" style={{ marginBottom: 0 }}>
              <Terminal size={18} color="#3395ff" />
              <span>Return Event Payload (Pydantic Schema)</span>
            </div>
          </div>
          <p className="card-desc">
            Raw <code>ReturnEvent</code> specification passed to <code>shield_engine.evaluate(event)</code>.
          </p>

          <textarea
            className="payload-editor"
            value={payloadText}
            onChange={(e) => setPayloadText(e.target.value)}
            rows={19}
            spellCheck={false}
          />

          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
            <button className="btn-primary" onClick={handleEvaluate} disabled={loading} style={{ flex: 1 }}>
              <Play size={16} fill="currentColor" />
              {loading ? 'Evaluating Return Risk...' : 'Evaluate Return Request'}
            </button>
          </div>

          {error && (
            <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--color-block)', borderRadius: 'var(--radius-md)', color: 'var(--color-block)', fontSize: '0.85rem' }}>
              <strong>Execution Error:</strong> {error}
            </div>
          )}
        </div>

        {/* Right Column: Real-Time Shield Verdict */}
        <div className="card">
          <div className="card-title">
            <ShieldAlert size={18} color="#3395ff" />
            <span>Shield Decision & Risk Diagnostics</span>
          </div>
          <p className="card-desc">
            Real-time defensive proxy verdict with sequential check breakdowns.
          </p>

          {!result && !loading && (
            <div style={{ padding: '3.5rem 1rem', textAlign: 'center', color: 'var(--text-dim)' }}>
              <ShieldAlert size={36} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
              <p>Execute an evaluation to inspect real-time risk scores and check triggers.</p>
            </div>
          )}

          {loading && (
            <div style={{ padding: '3.5rem 1rem', textAlign: 'center', color: 'var(--text-dim)' }}>
              <RefreshCw size={32} className="animate-spin" style={{ margin: '0 auto 1rem', color: 'var(--rzp-blue)' }} />
              <p>Executing sequential defensive checks in &lt;2ms...</p>
            </div>
          )}

          {result && !loading && (
            <div>
              {/* Verdict Header Banner */}
              <div
                style={{
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: '1.25rem',
                  background:
                    actionStr === 'BLOCK'
                      ? 'rgba(239, 68, 68, 0.15)'
                      : actionStr === 'FLAG' || actionStr === 'FLAGGED_FOR_INSPECTION'
                      ? 'rgba(245, 158, 11, 0.15)'
                      : 'rgba(16, 185, 129, 0.15)',
                  border: `1px solid ${
                    actionStr === 'BLOCK'
                      ? 'var(--color-block)'
                      : actionStr === 'FLAG' || actionStr === 'FLAGGED_FOR_INSPECTION'
                      ? 'var(--color-flag)'
                      : 'var(--color-allow)'
                  }`
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {actionStr === 'BLOCK' && <XCircle size={22} color="var(--color-block)" />}
                    {(actionStr === 'FLAG' || actionStr === 'FLAGGED_FOR_INSPECTION') && <AlertTriangle size={22} color="var(--color-flag)" />}
                    {(actionStr === 'ALLOW' || actionStr === 'AUTHORIZED') && <CheckCircle2 size={22} color="var(--color-allow)" />}
                    <span style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '0.5px' }}>
                      {actionStr === 'BLOCK'
                        ? 'BLOCKED (403 FORBIDDEN)'
                        : actionStr === 'FLAG' || actionStr === 'FLAGGED_FOR_INSPECTION'
                        ? 'FLAGGED FOR INSPECTION'
                        : 'AUTHORIZED (200 OK)'}
                    </span>
                  </div>
                  <span className="font-mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Risk: <strong>{riskScore}/100</strong>
                  </span>
                </div>
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: '#fff', lineHeight: 1.4 }}>
                  {decisionObj?.reason || result?.detail?.reason}
                </p>
              </div>

              {/* Sequential Defensive Checks List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
                {/* Check 1: Customer Return History */}
                <div style={{ padding: '0.75rem 1rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>1. Customer Return History & Velocity</span>
                    {(decisionObj?.triggered_checks || []).includes('SERIAL_RETURNER_FRAUD') ? (
                      <span className="badge badge-danger">FLAGGED / TRIGGERED</span>
                    ) : (
                      <span className="badge badge-success">PASSED</span>
                    )}
                  </div>
                </div>

                {/* Check 2: Wardrobing & Bracketing Abuse */}
                <div style={{ padding: '0.75rem 1rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>2. Wardrobing & Bracketing Abuse Check</span>
                    {(decisionObj?.triggered_checks || []).some(c => ['WARDROBING', 'BRACKETING_ABUSE'].includes(c)) ? (
                      <span className="badge badge-danger">TRIGGERED</span>
                    ) : (
                      <span className="badge badge-success">PASSED</span>
                    )}
                  </div>
                </div>

                {/* Check 3: Claim Anomaly & Damage */}
                <div style={{ padding: '0.75rem 1rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>3. Claim Anomaly & False Damage Check</span>
                    {(decisionObj?.triggered_checks || []).includes('FALSE_DAMAGE_CLAIM') ? (
                      <span className="badge badge-danger">TRIGGERED</span>
                    ) : (
                      <span className="badge badge-success">PASSED</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Meta Audit Box */}
              <div style={{ padding: '0.75rem 1rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <span>Audit Entry ID:</span>
                  <span className="font-mono" style={{ color: 'var(--rzp-blue)' }}>
                    {result?.data?.audit_id || result?.detail?.audit_id || 'N/A'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Event ID:</span>
                  <span className="font-mono">{result?.data?.event_id || result?.detail?.event_id || 'N/A'}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
