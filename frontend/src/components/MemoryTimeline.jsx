// MemoryTimeline.jsx — Browse all retained memories
import { useState, useEffect } from 'react';
import { getMemories } from '../api';

const TYPE_COLORS = {
  'incident postmortem': 'var(--red)',
  'deploy event':        'var(--amber)',
  'incident resolution': 'var(--green)',
  'engineer preference': 'var(--cyan)',
};

const TYPE_ICONS = {
  'incident postmortem': '🔴',
  'deploy event':        '📦',
  'incident resolution': '✅',
  'engineer preference': '💡',
};

export default function MemoryTimeline({ onToast }) {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    getMemories('').then((m) => { setMemories(m); setLoading(false); });
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    setSearching(true);
    const m = await getMemories(query);
    setMemories(m);
    setSearching(false);
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>// Memory Timeline</h1>
        <p>Everything Déjà Vu knows — incidents, deploys, resolutions, and engineer preferences.</p>
      </div>

      {/* Search */}
      <form className="memory-search-bar" onSubmit={handleSearch}>
        <input
          id="memory-search-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search memories… (e.g. payments-service, Redis, pool)"
        />
        <button className="btn btn-ghost" type="submit" disabled={searching} id="memory-search-btn">
          {searching ? '⟳' : '🔍'} Search
        </button>
      </form>

      {/* Stats row */}
      {!loading && (
        <div className="row" style={{ marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          {Object.entries(TYPE_ICONS).map(([type, icon]) => {
            const count = memories.filter((m) => m.type === type).length;
            return (
              <span key={type} style={{
                padding: '0.2rem 0.7rem',
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '20px',
                fontSize: '0.68rem',
                fontFamily: 'var(--font-mono)',
                color: TYPE_COLORS[type] || 'var(--text-muted)',
              }}>
                {icon} {count} {type}
              </span>
            );
          })}
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
          <span>Loading memory bank…</span>
        </div>
      )}

      {!loading && memories.length === 0 && (
        <div className="empty-state">
          <span className="icon">📭</span>
          <h3>No memories found</h3>
          <p>Seed the Hindsight bank or resolve incidents to populate memory.</p>
        </div>
      )}

      {!loading && memories.length > 0 && (
        <div className="memory-timeline-list">
          {memories.map((m, i) => (
            <div
              key={m.id || i}
              className="card"
              style={{ borderLeft: `3px solid ${TYPE_COLORS[m.type] || 'var(--border)'}` }}
            >
              <div className="row" style={{ justifyContent: 'space-between', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.4rem' }}>
                <div className="row" style={{ gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.9rem' }}>{TYPE_ICONS[m.type] || '📝'}</span>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    color: TYPE_COLORS[m.type] || 'var(--text-secondary)',
                  }}>
                    {m.id || '—'}
                  </span>
                  {m.service && (
                    <span className="service-chip active" style={{ padding: '0.1rem 0.5rem', cursor: 'default' }}>
                      {m.service}
                    </span>
                  )}
                  {m.severity && (
                    <span style={{
                      padding: '0.1rem 0.5rem',
                      background: 'var(--red-dim)',
                      color: 'var(--red)',
                      border: '1px solid rgba(255,61,87,0.2)',
                      borderRadius: '20px',
                      fontSize: '0.62rem',
                      fontFamily: 'var(--font-mono)',
                    }}>{m.severity}</span>
                  )}
                </div>
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {m.when || ''}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{m.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
