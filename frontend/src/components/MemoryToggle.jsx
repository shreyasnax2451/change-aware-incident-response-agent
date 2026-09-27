// MemoryToggle.jsx
export default function MemoryToggle({ enabled, onChange }) {
  return (
    <div className="memory-toggle-row">
      <div className="memory-toggle-label">
        <span>🧠 Hindsight Memory</span>
        <span>{enabled ? 'Active — recalling past incidents' : 'Disabled — generic LLM only'}</span>
      </div>
      <label className="toggle-switch" aria-label="Toggle memory">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span className="toggle-track" />
      </label>
    </div>
  );
}
