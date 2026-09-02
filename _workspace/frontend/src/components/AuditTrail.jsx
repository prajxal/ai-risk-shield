import React, { useState, useEffect } from 'react';
import { FileText, RefreshCw, ChevronDown, ChevronRight, CheckCircle, AlertTriangle, XCircle, Search, Terminal, ArrowRight } from 'lucide-react';

export default function AuditTrail({ refreshTrigger, onNavigateToSimulator }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDecision, setFilterDecision] = useState('ALL');
  const [autoPoll, setAutoPoll] = useState(true);

  const fetchLogs = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const res = await fetch('/audit-logs?limit=200');
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
        if (data.length > 0 && !expandedId) {
          setExpandedId(data[0].audit_id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  // Fetch on mount and whenever refreshTrigger changes
  useEffect(() => {
    fetchLogs();
  }, [refreshTrigger]);

  // Live polling every 3 seconds
  useEffect(() => {
    if (!autoPoll) return;
    const interval = setInterval(() => {
      fetchLogs(true);
    }, 3000);
    return () => clearInterval(interval);
  }, [autoPoll]);

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch =
      (log.transaction_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.agent_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.session_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.reason || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.audit_id || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDecision = filterDecision === 'ALL' || log.decision === filterDecision;

    return matchesSearch && matchesDecision;
  });

  return (
    <div className="audit-trail-container">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <div className="card-title" style={{ marginBottom: '0.25rem' }}>
              <FileText size={18} color="#3395ff" />
              <span>Structured Audit Trail ({logs.length} Recorded Transactions)</span>
            </div>
            <p className="card-desc" style={{ marginBottom: 0 }}>
              Immutable explainability logs capturing decision trace, policy triggers, and per-check diagnostic sub-objects (<code className="font-mono">_workspace/audit_logs/</code>).
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: 'var(--text-muted)', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={autoPoll}
                onChange={(e) => setAutoPoll(e.target.checked)}
              />
              Live Polling (3s)
            </label>
            <button className="btn-secondary" onClick={() => fetchLogs(false)} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              {loading ? 'Refreshing...' : 'Refresh Logs'}
            </button>
          </div>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '240px' }}>
            <input
              type="text"
              placeholder="Search by Tx ID, Agent ID, Session ID, or reason..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '0.6rem 1rem 0.6rem 2.5rem',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: '#fff',
                fontSize: '0.875rem'
              }}
            />
            <Search size={16} style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          </div>

          <select
            value={filterDecision}
            onChange={(e) => setFilterDecision(e.target.value)}
            style={{
              padding: '0.6rem 1rem',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              color: '#fff',
              fontSize: '0.875rem'
            }}
          >
            <option value="ALL">All Decisions ({logs.length})</option>
            <option value="ALLOW">ALLOW ({logs.filter(l => l.decision === 'ALLOW').length})</option>
            <option value="FLAG">FLAG ({logs.filter(l => l.decision === 'FLAG').length})</option>
            <option value="BLOCK">BLOCK ({logs.filter(l => l.decision === 'BLOCK').length})</option>
          </select>
        </div>

        {/* Empty State when no logs exist at all */}
        {logs.length === 0 ? (
          <div style={{
            padding: '4rem 2rem',
            textAlign: 'center',
            background: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-md)',
            border: '1px dashed var(--border-subtle)',
            color: 'var(--text-muted)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <FileText size={40} style={{ opacity: 0.3, color: 'var(--rzp-blue)' }} />
            <div style={{ maxWidth: '400px' }}>
              <strong style={{ fontSize: '1rem', color: '#fff', display: 'block', marginBottom: '0.5rem' }}>
                No transactions processed yet
              </strong>
              <p style={{ fontSize: '0.85rem' }}>
                Try a scenario in the Live Checkout Simulator to evaluate your first transaction and generate an audit record.
              </p>
            </div>
            {onNavigateToSimulator && (
              <button className="btn-primary" onClick={onNavigateToSimulator}>
                <Terminal size={16} />
                Open Live Checkout Simulator
                <ArrowRight size={14} />
              </button>
            )}
          </div>
        ) : filteredLogs.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-dim)' }}>
            No audit logs found matching "{searchTerm}".
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {filteredLogs.map((entry) => {
              const isExpanded = expandedId === entry.audit_id;
              const isAllow = entry.decision === 'ALLOW';
              const isFlag = entry.decision === 'FLAG';
              const isBlock = entry.decision === 'BLOCK';

              return (
                <div
                  key={entry.audit_id}
                  style={{
                    background: isExpanded ? 'var(--bg-card-hover)' : 'var(--bg-card)',
                    border: `1px solid ${isExpanded ? 'var(--border-highlight)' : (isBlock ? 'rgba(239, 68, 68, 0.25)' : (isFlag ? 'rgba(245, 158, 11, 0.25)' : 'var(--border-subtle)'))}`,
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {/* Summary Bar */}
                  <div
                    onClick={() => toggleExpand(entry.audit_id)}
                    style={{
                      padding: '1rem 1.25rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      gap: '1rem',
                      flexWrap: 'wrap'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {isExpanded ? <ChevronDown size={18} color="var(--rzp-blue)" /> : <ChevronRight size={18} color="var(--text-dim)" />}
                      <span className={`badge badge-${isAllow ? 'success' : (isFlag ? 'warning' : 'danger')}`} style={{ minWidth: '70px', justifyContent: 'center' }}>
                        {entry.decision}
                      </span>
                      <span className="font-mono" style={{ fontWeight: 700, fontSize: '0.9rem', color: '#fff' }}>
                        {entry.transaction_id}
                      </span>
                      <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        ({entry.audit_id})
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Agent: <span className="font-mono" style={{ color: '#fff' }}>{entry.agent_id}</span>
                      </span>
                      <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        {entry.timestamp}
                      </span>
                    </div>
                  </div>

                  {/* Expanded Detail Panel */}
                  {isExpanded && (
                    <div style={{ padding: '0 1.25rem 1.25rem 1.25rem', borderTop: '1px solid var(--border-subtle)' }}>
                      <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {/* Rationale */}
                        <div style={{
                          background: isAllow ? 'var(--color-allow-bg)' : (isFlag ? 'var(--color-flag-bg)' : 'var(--color-block-bg)'),
                          border: `1px solid ${isAllow ? 'var(--color-allow-border)' : (isFlag ? 'var(--color-flag-border)' : 'var(--color-block-border)')}`,
                          padding: '0.85rem 1rem',
                          borderRadius: 'var(--radius-sm)'
                        }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: isAllow ? 'var(--color-allow)' : (isFlag ? 'var(--color-flag)' : 'var(--color-block)'), textTransform: 'uppercase' }}>
                            Decision Rationale:
                          </span>
                          <p style={{ marginTop: '0.25rem', fontSize: '0.875rem', color: '#fff', lineHeight: 1.5 }}>
                            {entry.reason}
                          </p>
                        </div>

                        {/* Top Metadata */}
                        <div className="grid-3" style={{ fontSize: '0.8rem' }}>
                          <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                            <span style={{ color: 'var(--text-dim)' }}>Session ID:</span>
                            <div className="font-mono" style={{ color: '#fff', marginTop: '0.2rem' }}>{entry.session_id}</div>
                          </div>

                          <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                            <span style={{ color: 'var(--text-dim)' }}>Triggered Checks:</span>
                            <div className="font-mono" style={{ color: entry.triggered_checks?.length ? 'var(--color-block)' : 'var(--color-allow)', marginTop: '0.2rem' }}>
                              {entry.triggered_checks?.length ? entry.triggered_checks.join(', ') : 'None (Passed)'}
                            </div>
                          </div>

                          <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                            <span style={{ color: 'var(--text-dim)' }}>Audit Timestamp:</span>
                            <div className="font-mono" style={{ color: '#fff', marginTop: '0.2rem' }}>{entry.timestamp}</div>
                          </div>
                        </div>

                        {/* Check Details Sub-Objects */}
                        {entry.check_details && (
                          <div>
                            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem', display: 'block' }}>
                              Defensive Check Breakdown (check_details):
                            </span>
                            <div className="grid-3">
                              {/* 1. Injection Check */}
                              <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: `1px solid ${entry.check_details.injection_check?.passed ? 'transparent' : 'var(--color-block-border)'}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.8rem' }}>1. Injection Check</strong>
                                  <span className={`badge badge-${entry.check_details.injection_check?.passed ? 'success' : 'danger'}`}>
                                    {entry.check_details.injection_check?.passed ? 'PASS' : 'BLOCK'}
                                  </span>
                                </div>
                                <div className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div>Confidence: <span style={{ color: '#fff' }}>{((entry.check_details.injection_check?.confidence ?? 1.0) * 100).toFixed(0)}%</span></div>
                                  <div>Risk Score: <span style={{ color: (entry.check_details.injection_check?.risk_score || 0) > 0 ? 'var(--color-block)' : 'var(--color-allow)' }}>{entry.check_details.injection_check?.risk_score ?? 0}</span></div>
                                  {entry.check_details.injection_check?.indicators?.length > 0 && (
                                    <div style={{ marginTop: '0.25rem', color: 'var(--color-block)' }}>
                                      <strong>Threat:</strong> {entry.check_details.injection_check.indicators.join(', ')}
                                    </div>
                                  )}
                                  {entry.check_details.injection_check?.matched_surfaces?.length > 0 && (
                                    <div style={{ marginTop: '0.25rem', color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                                      {entry.check_details.injection_check.matched_surfaces[0]}
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* 2. Intent-Consistency Check */}
                              <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: `1px solid ${entry.check_details.intent_check?.passed ? 'transparent' : (entry.check_details.intent_check?.action === 'BLOCK' ? 'var(--color-block-border)' : 'var(--color-flag-border)')}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.8rem' }}>2. Intent Check</strong>
                                  <span className={`badge badge-${entry.check_details.intent_check?.passed ? 'success' : (entry.check_details.intent_check?.action === 'BLOCK' ? 'danger' : 'warning')}`}>
                                    {entry.check_details.intent_check?.passed ? 'PASS' : (entry.check_details.intent_check?.action || 'FLAG')}
                                  </span>
                                </div>
                                <div className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div>
                                    Budget Drift:{' '}
                                    <span style={{ color: (entry.check_details.intent_check?.budget_drift_pct || 0) > 50 ? 'var(--color-block)' : ((entry.check_details.intent_check?.budget_drift_pct || 0) > 10 ? 'var(--color-flag)' : 'var(--color-allow)'), fontWeight: 600 }}>
                                      {entry.check_details.intent_check?.budget_drift_pct !== undefined ? `${entry.check_details.intent_check.budget_drift_pct > 0 ? '+' : ''}${entry.check_details.intent_check.budget_drift_pct}%` : '0%'}
                                    </span>
                                  </div>
                                  <div>
                                    Semantic Match:{' '}
                                    <span style={{ color: (entry.check_details.intent_check?.item_similarity || 1.0) < 0.3 ? 'var(--color-block)' : '#fff' }}>
                                      {((entry.check_details.intent_check?.item_similarity ?? 1.0) * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                  <div>Cart Total: ₹{entry.check_details.intent_check?.actual_total?.toLocaleString() ?? 'N/A'} (Budget: ₹{entry.check_details.intent_check?.stated_budget?.toLocaleString() ?? 'N/A'})</div>
                                  {entry.check_details.intent_check?.quantity_drift > 0 && (
                                    <div style={{ color: 'var(--color-flag)' }}>Qty Drift: +{entry.check_details.intent_check.quantity_drift} units</div>
                                  )}
                                </div>
                              </div>

                              {/* 3. Velocity & Escalation Check */}
                              <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: `1px solid ${entry.check_details.velocity_check?.passed ? 'transparent' : (entry.check_details.velocity_check?.action === 'BLOCK' ? 'var(--color-block-border)' : 'var(--color-flag-border)')}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.8rem' }}>3. Velocity Check</strong>
                                  <span className={`badge badge-${entry.check_details.velocity_check?.passed ? 'success' : (entry.check_details.velocity_check?.action === 'BLOCK' ? 'danger' : 'warning')}`}>
                                    {entry.check_details.velocity_check?.passed ? 'PASS' : (entry.check_details.velocity_check?.action || 'FLAG')}
                                  </span>
                                </div>
                                <div className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div>
                                    Window Count:{' '}
                                    <span style={{ color: (entry.check_details.velocity_check?.window_count || 1) > 5 ? 'var(--color-block)' : ((entry.check_details.velocity_check?.window_count || 1) >= 3 ? 'var(--color-flag)' : '#fff'), fontWeight: 600 }}>
                                      {entry.check_details.velocity_check?.window_count ?? 1} tx / 60s
                                    </span>
                                  </div>
                                  <div>Retry Count: #{entry.check_details.velocity_check?.retry_count ?? 0}</div>
                                  {entry.check_details.velocity_check?.escalation_pct > 0 && (
                                    <div style={{ color: entry.check_details.velocity_check.escalation_pct > 50 ? 'var(--color-block)' : 'var(--color-flag)', fontWeight: 600 }}>
                                      Escalation: +{entry.check_details.velocity_check.escalation_pct}%
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Raw JSON Accordion */}
                        <div>
                          <details>
                            <summary style={{ cursor: 'pointer', fontSize: '0.75rem', color: 'var(--rzp-blue)', fontWeight: 600 }}>
                              View Complete Raw JSON Audit Record
                            </summary>
                            <pre className="code-block" style={{ marginTop: '0.5rem', maxHeight: '260px' }}>
                              {JSON.stringify(entry, null, 2)}
                            </pre>
                          </details>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
