import { useState } from 'react';
import { getWeaknessReport } from '../api';
import MemoryEvidence from './MemoryEvidence';

const SERVICES = [
  'payments-service',
  'checkout-api',
  'auth-service',
  'search-service',
  'notification-worker',
];

export default function ArchitectureReport({ onToast }) {
  const [service, setService] = useState('payments-service');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setReport(null);
    try {
      const data = await getWeaknessReport(service);
      setReport(data);
      onToast('Architecture report generated', 'success');
    } catch (e) {
      onToast('Failed to generate report: ' + e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>🏛 Architecture Weakness Report</h1>
        <p>Proactively analyze all past incidents for a service to identify structural flaws and suggest refactoring.</p>
      </div>

      <div className="split-layout">
        <div className="col">
          <div className="card">
            <div className="card-title">Select Service</div>
            <div className="field">
              <select
                value={service}
                onChange={(e) => setService(e.target.value)}
              >
                {SERVICES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={loading}
              style={{ width: '100%', marginTop: '1rem' }}
            >
              {loading ? 'Analyzing Memory…' : '🔍 Generate Report'}
            </button>
          </div>
        </div>

        <div className="col">
          {loading && (
            <div className="card">
              <div className="loading-overlay">
                <div className="spinner" />
                <span>Reflecting on past incidents…</span>
              </div>
            </div>
          )}

          {!loading && !report && (
            <div className="card">
              <div className="empty-state">
                <span className="icon">🏛</span>
                <h3>No report yet</h3>
                <p>Select a service to generate a structural weakness report based on its incident history.</p>
              </div>
            </div>
          )}

          {!loading && report && (
            <>
              <div className="card fade-in" style={{ borderTop: '2px solid var(--purple)' }}>
                <div className="card-title" style={{ color: 'var(--purple)' }}>Report: {report.service}</div>
                <pre style={{ whiteSpace: 'pre-wrap', background: 'var(--bg-card)', padding: '1rem', fontSize: '0.9rem', lineHeight: '1.5' }}>
                  {report.report_markdown}
                </pre>
              </div>
              
              <MemoryEvidence
                memories={report.memories_used}
                memoryEnabled={true}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
