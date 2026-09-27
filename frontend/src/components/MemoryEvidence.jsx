// MemoryEvidence.jsx
import { useState } from 'react';

const TYPE_TAG = {
  'incident postmortem': { label: 'Incident', cls: 'incident' },
  'deploy event':        { label: 'Deploy',   cls: 'deploy' },
  'incident resolution': { label: 'Resolution', cls: 'resolution' },
  'engineer preference': { label: 'Preference', cls: 'resolution' },
};

function MemoryItem({ mem }) {
  const [open, setOpen] = useState(false);
  const tag = TYPE_TAG[mem.type] || { label: mem.type, cls: 'incident' };

  return (
    <div className="memory-item">
      <div className="memory-item-header" onClick={() => setOpen((o) => !o)}>
        <div className="row" style={{ gap: '0.5rem' }}>
          <span className="memory-id">{mem.source || mem.id || '—'}</span>
          <span className={`memory-type-tag ${tag.cls}`}>{tag.label}</span>
        </div>
        <div className="row" style={{ gap: '0.75rem' }}>
          <span className="memory-when">{mem.when || ''}</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{open ? '▲' : '▼'}</span>
        </div>
      </div>
      {open && (
        <div className="memory-item-body slide-in">
          <p>{mem.text}</p>
          {mem.why_similar && (
            <div className="memory-why">Why relevant: {mem.why_similar}</div>
          )}
        </div>
      )}
    </div>
  );
}

export default function MemoryEvidence({ memories, memoryEnabled }) {
  if (!memoryEnabled) {
    return (
      <div className="card">
        <div className="card-title">Memory Evidence</div>
        <div className="memory-off-notice">
          <span className="icon">🧠</span>
          Memory is disabled. Toggle it ON to see institutional knowledge.
        </div>
      </div>
    );
  }

  if (!memories || memories.length === 0) {
    return (
      <div className="card">
        <div className="card-title">Memory Evidence</div>
        <div className="empty-state">
          <span className="icon">📭</span>
          <h3>No memories retrieved</h3>
          <p>Run an analysis first to see which past incidents informed this response.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">
        Memory Evidence
        <span style={{
          marginLeft: 'auto',
          fontSize: '0.68rem',
          color: 'var(--cyan)',
          fontFamily: 'var(--font-mono)',
        }}>
          {memories.length} memories used
        </span>
      </div>
      <div className="memory-evidence">
        {memories.map((m, i) => (
          <MemoryItem key={m.source || m.id || i} mem={m} />
        ))}
      </div>
    </div>
  );
}
