// App.jsx — Root component with navigation and toast system
import { useState, useEffect, useCallback } from 'react';
import './styles.css';
import IncidentConsole from './components/IncidentConsole';
import ChangeReview from './components/ChangeReview';
import PlaybookView from './components/PlaybookView';
import MemoryTimeline from './components/MemoryTimeline';
import { healthCheck } from './api';

const PAGES = [
  { id: 'triage',   label: 'Incident Console', icon: '⚡' },
  { id: 'risk',     label: 'Change Review',    icon: '🛡' },
  { id: 'playbook', label: 'Playbooks',        icon: '📖' },
  { id: 'memory',   label: 'Memory',           icon: '🧠' },
];

// ─── Toast system ─────────────────────────────────────────────────────────────
let _toastId = 0;

function ToastContainer({ toasts }) {
  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.type}`}>
          {t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : 'ℹ'} {t.message}
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState('triage');
  const [toasts, setToasts] = useState([]);
  const [health, setHealth] = useState(null);

  // Health check on mount
  useEffect(() => {
    healthCheck().then(setHealth);
  }, []);

  const addToast = useCallback((message, type = 'info') => {
    const id = ++_toastId;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const isOnline = health &&
    !String(health.hindsight || '').includes('offline') &&
    !String(health.groq || '').includes('offline');

  const renderPage = () => {
    switch (page) {
      case 'triage':   return <IncidentConsole onToast={addToast} />;
      case 'risk':     return <ChangeReview onToast={addToast} />;
      case 'playbook': return <PlaybookView onToast={addToast} />;
      case 'memory':   return <MemoryTimeline onToast={addToast} />;
      default:         return null;
    }
  };

  return (
    <div className="app-layout">
      {/* ── Navbar ── */}
      <nav className="navbar" role="navigation" aria-label="Main navigation">
        <a className="navbar-brand" href="#" onClick={(e) => { e.preventDefault(); setPage('triage'); }}>
          <span className="brand-icon">🧠</span>
          <span className="brand-name">DÉJÀ VU</span>
          {/* <span className="brand-tag">by Kirana Cart SRE</span> */}
        </a>

        <ul className="navbar-nav" role="list">
          {PAGES.map((p) => (
            <li key={p.id}>
              <button
                className={`nav-btn ${page === p.id ? 'active' : ''}`}
                onClick={() => setPage(p.id)}
                id={`nav-${p.id}`}
                aria-current={page === p.id ? 'page' : undefined}
              >
                {p.icon} {p.label}
              </button>
            </li>
          ))}
        </ul>

        <div className="navbar-status">
          <span className={`status-dot ${health === null ? 'checking' : isOnline ? '' : 'offline'}`} />
          <span>
            {health === null
              ? 'checking…'
              : isOnline
              ? 'live mode'
              : 'mock mode'}
          </span>
        </div>
      </nav>

      {/* ── Main content ── */}
      <main className="main-content" id="main-content">
        {renderPage()}
      </main>

      <ToastContainer toasts={toasts} />
    </div>
  );
}
