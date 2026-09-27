// PlaybookView.jsx — Living service playbooks
import { useState, useEffect } from 'react';
import { getPlaybook, refreshPlaybook } from '../api';

const SERVICES = [
  'payments-service',
  'checkout-api',
  'auth-service',
  'search-service',
  'notification-worker',
];

function diffLines(prev, curr) {
  if (!prev) return curr.split('\n').map((l) => ({ type: 'same', text: l }));
  const prevLines = prev.split('\n');
  const currLines = curr.split('\n');
  const result = [];
  // Simple line-by-line diff (sufficient for demo)
  const maxLen = Math.max(prevLines.length, currLines.length);
  for (let i = 0; i < maxLen; i++) {
    const p = prevLines[i];
    const c = currLines[i];
    if (p === undefined) result.push({ type: 'add', text: c });
    else if (c === undefined) result.push({ type: 'remove', text: p });
    else if (p !== c) {
      result.push({ type: 'remove', text: p });
      result.push({ type: 'add', text: c });
    } else {
      result.push({ type: 'same', text: c });
    }
  }
  return result;
}

export default function PlaybookView({ onToast }) {
  const [activeService, setActiveService] = useState(SERVICES[0]);
  const [playbook, setPlaybook] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [tab, setTab] = useState('current'); // current | diff

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setPlaybook(null);
    getPlaybook(activeService).then((p) => {
      if (!cancelled) { setPlaybook(p); setLoading(false); }
    });
    return () => { cancelled = true; };
  }, [activeService]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const p = await refreshPlaybook(activeService);
      setPlaybook(p);
      onToast('Playbook refreshed from memory', 'success');
    } catch {
      onToast('Refresh failed', 'error');
    } finally {
      setRefreshing(false);
    }
  };

  const diffed = playbook ? diffLines(playbook.previous, playbook.current) : [];
  const hasPrevious = playbook?.previous && playbook.previous !== playbook.current;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>// Service Playbooks</h1>
        <p>Living runbooks built from incident memory — auto-updated after each resolution.</p>
      </div>

      {/* Service selector */}
      <div className="service-selector">
        {SERVICES.map((s) => (
          <button
            key={s}
            className={`service-chip ${s === activeService ? 'active' : ''}`}
            onClick={() => { setActiveService(s); setTab('current'); }}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="card">
        <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <span>Playbook — {activeService}</span>
          <div className="row">
            {playbook && (
              <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                Updated {playbook.updated_at ? new Date(playbook.updated_at).toLocaleDateString('en-IN', { day:'numeric', month:'short', hour:'2-digit', minute:'2-digit' }) : '—'}
              </span>
            )}
            <button
              className="btn btn-ghost btn-sm"
              onClick={handleRefresh}
              disabled={refreshing || loading}
              id="playbook-refresh-btn"
            >
              {refreshing ? '⟳ Refreshing…' : '⟳ Refresh from Memory'}
            </button>
          </div>
        </div>

        {loading && (
          <div className="loading-overlay">
            <div className="spinner" />
            <span>Loading playbook…</span>
          </div>
        )}

        {!loading && playbook && (
          <>
            {/* Tabs */}
            <div className="playbook-tabs">
              <button
                className={`playbook-tab ${tab === 'current' ? 'active' : ''}`}
                onClick={() => setTab('current')}
              >
                Current (v{hasPrevious ? '3' : '1'})
              </button>
              {hasPrevious && (
                <button
                  className={`playbook-tab ${tab === 'diff' ? 'active' : ''}`}
                  onClick={() => setTab('diff')}
                  id="playbook-diff-tab"
                >
                  v2 → v3 Changes
                </button>
              )}
            </div>

            {tab === 'current' && (
              <pre className="playbook-content">{playbook.current}</pre>
            )}

            {tab === 'diff' && (
              <pre className="playbook-content">
                {diffed.map((line, i) => {
                  if (line.type === 'add')    return <span key={i} className="playbook-diff-add">{`+ ${line.text}\n`}</span>;
                  if (line.type === 'remove') return <span key={i} className="playbook-diff-remove">{`- ${line.text}\n`}</span>;
                  return <span key={i}>{`  ${line.text}\n`}</span>;
                })}
              </pre>
            )}
          </>
        )}
      </div>
    </div>
  );
}
