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

export default function MemoryTimeline({ onToast, globalMemories }) {
  const [memories, setMemories] = useState(globalMemories || []);
  const [query, setQuery] = useState('');

  // Update local memories if globalMemories loads after mount
  useEffect(() => {
    if (globalMemories && !query) {
      setMemories(globalMemories);
    }
  }, [globalMemories, query]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setMemories(globalMemories);
      return;
    }
    const q = query.toLowerCase();
    const filtered = globalMemories.filter((m) => 
      (m.text && m.text.toLowerCase().includes(q)) ||
      (m.service && m.service.toLowerCase().includes(q)) ||
      (m.id && m.id.toLowerCase().includes(q)) ||
      (m.type && m.type.toLowerCase().includes(q))
    );
    setMemories(filtered);
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>// Memory Timeline</h1>
        <p>Everything OnCall AI knows — incidents, deploys, resolutions, and engineer preferences.</p>
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
        <button className="btn btn-ghost" type="submit" id="memory-search-btn">
          🔍 Search
        </button>
      </form>

      {/* Stats row */}
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


      {memories.length === 0 && (
        <div className="empty-state">
          <span className="icon">📭</span>
          <h3>No memories found</h3>
          <p>Seed the Hindsight bank or resolve incidents to populate memory.</p>
        </div>
      )}

      {memories.length > 0 && (
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
