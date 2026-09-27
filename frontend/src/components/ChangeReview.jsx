// ChangeReview.jsx — Pre-deploy risk check screen
import { useState } from 'react';
import { riskCheck } from '../api';
import MemoryToggle from './MemoryToggle';
import MemoryEvidence from './MemoryEvidence';

const SERVICES = [
  'payments-service',
  'checkout-api',
  'auth-service',
  'search-service',
  'notification-worker',
];

const DEMO_PR = {
  service: 'payments-service',
  change_description: 'Reduce DB connection pool from 50 to 25 to cut RDS cost by ~30%. Change: maximumPoolSize: 50 → 25 in payments-service HikariCP config.',
  diff: `--- a/config/payments-service.yaml
+++ b/config/payments-service.yaml
@@ -14,7 +14,7 @@ datasource:
   hikari:
-    maximumPoolSize: 50
+    maximumPoolSize: 25
     minimumIdle: 5
     connectionTimeout: 30000`,
};

export default function ChangeReview({ onToast }) {
  const [service, setService] = useState(DEMO_PR.service);
  const [changeDesc, setChangeDesc] = useState(DEMO_PR.change_description);
  const [diff, setDiff] = useState(DEMO_PR.diff);
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleCheck = async () => {
    if (!changeDesc.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const r = await riskCheck({ service, change_description: changeDesc, diff, use_memory: memoryEnabled });
      setResult(r);
      onToast('Risk assessment complete', 'info');
    } catch (e) {
      onToast('Risk check failed: ' + e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const riskColors = {
    high:   { color: 'var(--red)',   icon: '🔴' },
    medium: { color: 'var(--amber)', icon: '🟡' },
    low:    { color: 'var(--green)', icon: '🟢' },
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>// Change Review</h1>
        <p>Paste a PR description or diff — Déjà Vu surfaces past incidents caused by similar changes.</p>
      </div>

      <div className="split-layout">
        {/* ── Left: inputs ── */}
        <div className="col">
          <div className="card">
            <div className="card-title">Change Details</div>

            <div className="field">
              <label className="field-label" htmlFor="cr-service">Service</label>
              <select id="cr-service" value={service} onChange={(e) => setService(e.target.value)}>
                {SERVICES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="cr-desc">PR Title / Description</label>
              <textarea
                id="cr-desc"
                value={changeDesc}
                onChange={(e) => setChangeDesc(e.target.value)}
                placeholder="Describe the change being deployed…"
                rows={5}
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="cr-diff">Diff Snippet (optional)</label>
              <textarea
                id="cr-diff"
                value={diff}
                onChange={(e) => setDiff(e.target.value)}
                placeholder="Paste a relevant diff…"
                rows={7}
                style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}
              />
            </div>

            <MemoryToggle enabled={memoryEnabled} onChange={setMemoryEnabled} />

            <button
              id="risk-check-btn"
              className="btn btn-primary"
              onClick={handleCheck}
              disabled={loading || !changeDesc.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                  Scanning incident history…
                </>
              ) : (
                '🔍 Check Risk'
              )}
            </button>
          </div>
        </div>

        {/* ── Right: results ── */}
        <div className="col">
          {loading && (
            <div className="card">
              <div className="loading-overlay">
                <div className="spinner" />
                <span>Scanning incident history…</span>
              </div>
            </div>
          )}

          {!loading && !result && (
            <div className="card">
              <div className="empty-state">
                <span className="icon">🛡</span>
                <h3>No risk assessment yet</h3>
                <p>Fill in the change details and click Check Risk to see what memory says about similar past deploys.</p>
              </div>
            </div>
          )}

          {!loading && result && (
            <>
              <div className="card">
                <div className="card-title">Risk Assessment</div>
                <div className="col">
                  {/* Risk badge */}
                  <div className="row">
                    <span className={`risk-badge ${result.risk_level}`}>
                      {riskColors[result.risk_level]?.icon} {result.risk_level} risk
                    </span>
                    {!memoryEnabled && (
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        (memory disabled)
                      </span>
                    )}
                  </div>

                  {/* Spoken summary */}
                  <div className="spoken-summary">
                    <span className="spoken-icon">💬</span>
                    <span className="spoken-text">{result.spoken_summary}</span>
                  </div>

                  {/* Evidence timeline */}
                  {result.evidence?.length > 0 && (
                    <div>
                      <div className="label" style={{ marginBottom: '0.75rem' }}>
                        Past incidents triggered by similar changes
                      </div>
                      <div className="evidence-timeline">
                        {result.evidence.map((ev) => (
                          <div key={ev.id} className="evidence-item">
                            <div className="evidence-item-header">
                              <span className="evidence-item-id">{ev.id}</span>
                              <span className="evidence-item-date">{ev.when}</span>
                            </div>
                            <p className="evidence-item-text">{ev.what_happened}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {result.recommendation?.length > 0 && (
                    <div className="fix-list">
                      <div className="label">Recommendations</div>
                      <ol>
                        {result.recommendation.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ol>
                    </div>
                  )}

                  {/* Watch metrics */}
                  {result.watch_metrics?.length > 0 && (
                    <div>
                      <div className="label" style={{ marginBottom: '0.5rem' }}>Watch these metrics</div>
                      <div className="watch-metrics">
                        {result.watch_metrics.map((m, i) => (
                          <span key={i} className="metric-chip">{m}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Diff box */}
                  {diff.trim() && (
                    <div>
                      <div className="label" style={{ marginBottom: '0.4rem' }}>Change Diff</div>
                      <div className="diff-box">
                        {diff.split('\n').map((line, i) => {
                          const cls = line.startsWith('+') ? 'add' : line.startsWith('-') ? 'remove' : 'context';
                          return <span key={i} className={cls}>{line}{'\n'}</span>;
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <MemoryEvidence
                memories={result.memories_used}
                memoryEnabled={memoryEnabled}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
