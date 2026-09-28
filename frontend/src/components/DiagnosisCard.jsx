// DiagnosisCard.jsx
import { useState, useEffect } from 'react';
import { speak } from '../api';

export default function DiagnosisCard({ diagnosis }) {
  const [speaking, setSpeaking] = useState(false);

  if (!diagnosis) return null;

  const {
    matched,
    root_cause,
    recommended_fix,
    avoid,
    similar_incidents,
    suspect_change,
    confidence,
    spoken_summary,
    auto_fix_script,
  } = diagnosis;

  const handleSpeak = async () => {
    if (speaking) return;
    setSpeaking(true);
    try {
      const url = await speak(spoken_summary);
      if (url) {
        const audio = new Audio(url);
        audio.onended = () => setSpeaking(false);
        audio.play();
      } else {
        // Browser TTS fallback
        const utt = new SpeechSynthesisUtterance(spoken_summary);
        utt.onend = () => setSpeaking(false);
        speechSynthesis.speak(utt);
      }
    } catch {
      setSpeaking(false);
    }
  };

  useEffect(() => {
    if (spoken_summary) {
      handleSpeak();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spoken_summary]);

  return (
    <div className="diagnosis-card fade-in">
      {/* Header row */}
      <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div className="row">
          <span className={`confidence-badge ${confidence}`}>
            {confidence === 'high' ? '◉' : confidence === 'medium' ? '◎' : '○'} {confidence} confidence
          </span>
          {matched && (
            <span className="confidence-badge high" style={{ background: 'rgba(0,200,220,0.1)', color: 'var(--cyan)', borderColor: 'rgba(0,200,220,0.25)' }}>
              ✓ memory match
            </span>
          )}
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={handleSpeak}
          disabled={speaking}
          title="Read aloud"
        >
          {speaking ? '🔊 Speaking…' : '🔊 Listen'}
        </button>
      </div>

      {/* Spoken summary */}
      <div className="spoken-summary">
        <span className="spoken-icon">💬</span>
        <span className="spoken-text">{spoken_summary}</span>
      </div>

      {/* Root cause */}
      <div className="root-cause-box">
        <div className="label">Root Cause</div>
        <p className="root-cause-text">{root_cause}</p>
        {suspect_change && (
          <div className="suspect-change">
            ⚠ Suspect change: {suspect_change}
          </div>
        )}
      </div>

      {/* Recommended fixes */}
      {recommended_fix?.length > 0 && (
        <div className="fix-list">
          <div className="label">Recommended Fix</div>
          <ol>
            {recommended_fix.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Auto-fix script */}
      {auto_fix_script && (
        <div className="fix-list" style={{ marginTop: '1rem', background: 'rgba(0,255,0,0.05)', borderLeft: '2px solid var(--green)' }}>
          <div className="label" style={{ color: 'var(--green)' }}>✨ Auto-Remediation Script</div>
          <pre style={{ background: '#000', padding: '1rem', overflowX: 'auto', borderRadius: 'var(--radius-sm)', marginTop: '0.5rem' }}>
            <code>{auto_fix_script}</code>
          </pre>
        </div>
      )}

      {/* Avoid */}
      {avoid?.length > 0 && (
        <div className="avoid-list">
          <div className="label">⚠ Do NOT do these</div>
          <ul>
            {avoid.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Similar incidents */}
      {similar_incidents?.length > 0 && (
        <div>
          <div className="label" style={{ marginBottom: '0.6rem' }}>Similar Past Incidents</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {similar_incidents.map((inc) => (
              <div key={inc.id} style={{
                padding: '0.5rem 0.75rem',
                background: 'rgba(0,0,0,0.3)',
                borderRadius: 'var(--radius-sm)',
                borderLeft: '2px solid var(--cyan)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.2rem',
              }}>
                <div className="row" style={{ justifyContent: 'space-between' }}>
                  <span className="text-mono" style={{ color: 'var(--cyan)', fontSize: '0.75rem', fontWeight: 600 }}>{inc.id}</span>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{inc.when}</span>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{inc.why_similar}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
