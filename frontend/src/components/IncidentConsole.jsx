// IncidentConsole.jsx — Main triage screen
import { useState } from 'react';
import { triage, resolve } from '../api';
import MemoryToggle from './MemoryToggle';
import PushToTalk from './PushToTalk';
import DiagnosisCard from './DiagnosisCard';
import MemoryEvidence from './MemoryEvidence';

const SERVICES = [
  'payments-service',
  'checkout-api',
  'auth-service',
  'search-service',
  'notification-worker',
];

const DEMO_ALERT = `CRITICAL: payments-service — HikariPool-1 connection timeouts
PagerDuty: p99 latency > 3s | Error rate 34% on /checkout
Detected: 2026-09-28T01:47:00+05:30
Logs: HikariPool-1 - Connection is not available, request timed out after 30000ms
      java.sql.SQLTransientConnectionException: payments-ds - Connection is not available
Recent deploy: DEP-901 by Matrix (47 min ago) — "Reduce DB pool max from 50 to 25 to cut RDS cost"`;

export default function IncidentConsole({ onToast }) {
  const [alertText, setAlertText] = useState(DEMO_ALERT);
  const [service, setService] = useState('payments-service');
  const [engineer, setEngineer] = useState('Ravi');
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);
  const [resolveOpen, setResolveOpen] = useState(false);
  const [resolveForm, setResolveForm] = useState({ worked: '', failed: '', notes: '' });
  const [resolving, setResolving] = useState(false);
  const [incidentId, setIncidentId] = useState(null);

  const handleAnalyze = async () => {
    if (!alertText.trim()) return;
    setLoading(true);
    setDiagnosis(null);
    try {
      const result = await triage({ alert_text: alertText, service, use_memory: memoryEnabled, engineer });
      setDiagnosis(result);
      setIncidentId('INC-' + Date.now().toString().slice(-4));
      onToast('Analysis complete', 'info');
    } catch (e) {
      onToast('Analysis failed: ' + e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceTranscript = (text) => {
    // Append to alert text or use as-is if empty
    setAlertText((prev) => (prev.trim() ? prev + '\n\nVoice note: ' + text : text));
  };

  const handleResolve = async () => {
    if (!resolveForm.worked.trim()) {
      onToast('Please enter what worked', 'error');
      return;
    }
    setResolving(true);
    try {
      await resolve({
        incident_id: incidentId,
        alert_text: alertText,
        service,
        worked: resolveForm.worked,
        failed: resolveForm.failed,
        notes: resolveForm.notes,
        engineer,
      });
      onToast('✓ Resolution saved to memory', 'success');
      setResolveOpen(false);
      setResolveForm({ worked: '', failed: '', notes: '' });
    } catch (e) {
      onToast('Failed to save resolution', 'error');
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>// Incident Console</h1>
        <p>Paste an alert, speak it, or use the demo payload — Déjà Vu recalls what happened before.</p>
      </div>

      <div className="split-layout">
        {/* ── Left panel: inputs ── */}
        <div className="col">
          <div className="card">
            <div className="card-title">Alert Input & Controls</div>

            <div className="field">
              <label className="field-label" htmlFor="alert-text">Alert / Error Log</label>
              <textarea
                id="alert-text"
                value={alertText}
                onChange={(e) => setAlertText(e.target.value)}
                placeholder="Paste PagerDuty alert, error log, or describe the incident…"
                rows={9}
              />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="service-select">Service</label>
              <select
                id="service-select"
                value={service}
                onChange={(e) => setService(e.target.value)}
              >
                {SERVICES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="engineer-name">Engineer on call</label>
              <input
                id="engineer-name"
                type="text"
                value={engineer}
                onChange={(e) => setEngineer(e.target.value)}
                placeholder="Your name"
              />
            </div>

            <MemoryToggle enabled={memoryEnabled} onChange={setMemoryEnabled} />
            <PushToTalk onTranscript={handleVoiceTranscript} disabled={loading} />

            <button
              id="analyze-btn"
              className="btn btn-primary"
              onClick={handleAnalyze}
              disabled={loading || !alertText.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                  Checking past incidents…
                </>
              ) : (
                '⚡ Analyze Incident'
              )}
            </button>
          </div>

          {/* Resolve drawer */}
          {diagnosis && (
            <div className="resolve-drawer">
              <div
                className="resolve-drawer-header"
                onClick={() => setResolveOpen((o) => !o)}
                id="resolve-toggle"
              >
                <span>✓ Mark as Resolved — Save to Memory</span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                  {resolveOpen ? '▲' : '▼'}
                </span>
              </div>
              {resolveOpen && (
                <div className="resolve-drawer-body slide-in">
                  <div className="field">
                    <label className="field-label">What worked?</label>
                    <input
                      type="text"
                      id="resolve-worked"
                      value={resolveForm.worked}
                      onChange={(e) => setResolveForm((f) => ({ ...f, worked: e.target.value }))}
                      placeholder="e.g. Rolled back DEP-901"
                    />
                  </div>
                  <div className="field">
                    <label className="field-label">What failed? (optional)</label>
                    <input
                      type="text"
                      id="resolve-failed"
                      value={resolveForm.failed}
                      onChange={(e) => setResolveForm((f) => ({ ...f, failed: e.target.value }))}
                      placeholder="e.g. Pod restarts did not help"
                    />
                  </div>
                  <div className="field">
                    <label className="field-label">Notes (optional)</label>
                    <textarea
                      id="resolve-notes"
                      value={resolveForm.notes}
                      onChange={(e) => setResolveForm((f) => ({ ...f, notes: e.target.value }))}
                      placeholder="Any additional context…"
                      rows={3}
                    />
                  </div>
                  <button
                    className="btn btn-primary"
                    onClick={handleResolve}
                    disabled={resolving}
                    id="resolve-submit-btn"
                  >
                    {resolving ? 'Saving…' : '💾 Save Resolution to Memory'}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Right panel: results ── */}
        <div className="col">
          {loading && (
            <div className="card">
              <div className="loading-overlay">
                <div className="spinner" />
                <span>Checking past incidents…</span>
              </div>
            </div>
          )}

          {!loading && !diagnosis && (
            <div className="card">
              <div className="empty-state">
                <span className="icon">🔍</span>
                <h3>No analysis yet</h3>
                <p>Enter an alert and click Analyze to see Déjà Vu recall similar incidents from memory.</p>
              </div>
            </div>
          )}

          {!loading && diagnosis && (
            <>
              <div className="card">
                <div className="card-title">Incident Diagnosis</div>
                <DiagnosisCard diagnosis={diagnosis} />
              </div>
              <MemoryEvidence
                memories={diagnosis.memories_used}
                memoryEnabled={memoryEnabled}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
