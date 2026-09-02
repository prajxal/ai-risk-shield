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
    const idKey = log.event_id || log.transaction_id || '';
    const custKey = log.customer_id || log.agent_id || '';
    const matchesSearch =
      idKey.toLowerCase().includes(searchTerm.toLowerCase()) ||
      custKey.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.order_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.return_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
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
              <span>Structured Return-Risk Audit Trail ({logs.length} Recorded Return Events)</span>
            </div>
            <p className="card-desc" style={{ marginBottom: 0 }}>
              Immutable explainability logs capturing return decision traces, check triggers, and diagnostic sub-objects (<code className="font-mono">_workspace/audit_logs/</code>).
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
              placeholder="Search by Event ID, Customer ID, Order ID, or reason..."
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

        {/* Empty State when no logs exist */}
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
                No return events evaluated yet
              </strong>
              <p style={{ fontSize: '0.85rem' }}>
                Try a scenario in the Return Simulator to evaluate your first return request and generate an audit record.
              </p>
            </div>
            {onNavigateToSimulator && (
              <button className="btn-primary" onClick={onNavigateToSimulator}>
                <Terminal size={16} />
                Open Return Simulator
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
              const eventId = entry.event_id || entry.transaction_id;
              const customerId = entry.customer_id || entry.agent_id;

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
                        {eventId}
                      </span>
                      <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        ({entry.audit_id})
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Customer: <span className="font-mono" style={{ color: '#fff' }}>{customerId}</span>
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
                            <span style={{ color: 'var(--text-dim)' }}>Order / Return ID:</span>
                            <div className="font-mono" style={{ color: '#fff', marginTop: '0.2rem' }}>
                              {entry.order_id || 'N/A'} • {entry.return_id || 'N/A'}
                            </div>
                          </div>

                          <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                            <span style={{ color: 'var(--text-dim)' }}>Triggered Checks:</span>
                            <div className="font-mono" style={{ color: entry.triggered_checks?.length ? 'var(--color-block)' : 'var(--color-allow)', marginTop: '0.2rem' }}>
                              {entry.triggered_checks?.length ? entry.triggered_checks.join(', ') : 'None (Legitimate Return)'}
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
                              Defensive Return-Risk Check Breakdown:
                            </span>
                            <div className="grid-3">
                              {/* 1. Customer History Check */}
                              <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: `1px solid ${entry.check_details.customer_history_check?.passed ? 'transparent' : (entry.check_details.customer_history_check?.action === 'BLOCK' ? 'var(--color-block-border)' : 'var(--color-flag-border)')}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.8rem' }}>1. Customer History</strong>
                                  <span className={`badge badge-${entry.check_details.customer_history_check?.passed ? 'success' : (entry.check_details.customer_history_check?.action === 'BLOCK' ? 'danger' : 'warning')}`}>
                                    {entry.check_details.customer_history_check?.passed ? 'PASS' : (entry.check_details.customer_history_check?.action || 'FLAG')}
                                  </span>
                                </div>
                                <div className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div>Return Rate: <span style={{ color: '#fff' }}>{((entry.check_details.customer_history_check?.historical_return_rate || 0) * 100).toFixed(1)}%</span></div>
                                  <div>Chargebacks: <span style={{ color: (entry.check_details.customer_history_check?.chargeback_count || 0) > 0 ? 'var(--color-block)' : '#fff' }}>{entry.check_details.customer_history_check?.chargeback_count ?? 0}</span></div>
                                  <div>Account Age: {entry.check_details.customer_history_check?.account_age_days ?? 'N/A'} days</div>
                                </div>
                              </div>

                              {/* 2. Wardrobing / Bracketing Check */}
                              <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: `1px solid ${entry.check_details.wardrobing_bracketing_check?.passed ? 'transparent' : (entry.check_details.wardrobing_bracketing_check?.action === 'BLOCK' ? 'var(--color-block-border)' : 'var(--color-flag-border)')}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.8rem' }}>2. Wardrobing & Bracketing</strong>
                                  <span className={`badge badge-${entry.check_details.wardrobing_bracketing_check?.passed ? 'success' : (entry.check_details.wardrobing_bracketing_check?.action === 'BLOCK' ? 'danger' : 'warning')}`}>
                                    {entry.check_details.wardrobing_bracketing_check?.passed ? 'PASS' : (entry.check_details.wardrobing_bracketing_check?.action || 'FLAG')}
                                  </span>
                                </div>
                                <div className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div>Wardrobing Risk: <span style={{ color: entry.check_details.wardrobing_bracketing_check?.is_wardrobing ? 'var(--color-block)' : '#fff' }}>{entry.check_details.wardrobing_bracketing_check?.is_wardrobing ? 'DETECTED' : 'CLEAR'}</span></div>
                                  <div>Bracketing Risk: <span style={{ color: entry.check_details.wardrobing_bracketing_check?.is_bracketing ? 'var(--color-flag)' : '#fff' }}>{entry.check_details.wardrobing_bracketing_check?.is_bracketing ? 'DETECTED' : 'CLEAR'}</span></div>
                                  <div>Holding Time: {entry.check_details.wardrobing_bracketing_check?.days_held ?? entry.check_details.wardrobing_bracketing_check?.days_since_purchase ?? 'N/A'} days</div>
                                </div>
                              </div>

                              {/* 3. Claim Anomaly Check */}
                              <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: `1px solid ${entry.check_details.claim_anomaly_check?.passed ? 'transparent' : (entry.check_details.claim_anomaly_check?.action === 'BLOCK' ? 'var(--color-block-border)' : 'var(--color-flag-border)')}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.8rem' }}>3. Claim Anomaly</strong>
                                  <span className={`badge badge-${entry.check_details.claim_anomaly_check?.passed ? 'success' : (entry.check_details.claim_anomaly_check?.action === 'BLOCK' ? 'danger' : 'warning')}`}>
                                    {entry.check_details.claim_anomaly_check?.passed ? 'PASS' : (entry.check_details.claim_anomaly_check?.action || 'FLAG')}
                                  </span>
                                </div>
                                <div className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                  <div>Tag Condition: <span style={{ color: '#fff' }}>{entry.check_details.claim_anomaly_check?.condition || 'TAGS_ATTACHED'}</span></div>
                                  <div>Refund Destination: {entry.check_details.claim_anomaly_check?.refund_destination || 'ORIGINAL'}</div>
                                  <div>Risk Score: <span style={{ color: (entry.check_details.claim_anomaly_check?.risk_score || 0) > 0 ? 'var(--color-block)' : 'var(--color-allow)' }}>{entry.check_details.claim_anomaly_check?.risk_score ?? 0}</span></div>
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
