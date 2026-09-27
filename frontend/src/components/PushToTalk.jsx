// PushToTalk.jsx
import { useState, useRef, useCallback } from 'react';
import { transcribeAudio } from '../api';

export default function PushToTalk({ onTranscript, disabled }) {
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState('idle'); // idle | recording | processing
  const [transcript, setTranscript] = useState('');
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = useCallback(async () => {
    if (disabled || recording) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setStatus('processing');
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        try {
          const result = await transcribeAudio(blob);
          setTranscript(result.text);
          onTranscript(result.text);
        } catch (e) {
          setTranscript('(transcription failed)');
        }
        setStatus('idle');
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
      setStatus('recording');
      setTranscript('');
    } catch {
      alert('Microphone access denied. Please allow microphone access.');
    }
  }, [disabled, recording, onTranscript]);

  const stopRecording = useCallback(() => {
    if (!recording || !mediaRecorderRef.current) return;
    mediaRecorderRef.current.stop();
    setRecording(false);
  }, [recording]);

  const statusText = {
    idle: 'PUSH TO TALK',
    recording: '● RECORDING…',
    processing: '⟳ PROCESSING…',
  }[status];

  return (
    <div className="ptt-section">
      <button
        className={`ptt-btn ${recording ? 'recording' : ''}`}
        onMouseDown={startRecording}
        onMouseUp={stopRecording}
        onTouchStart={startRecording}
        onTouchEnd={stopRecording}
        disabled={disabled || status === 'processing'}
        aria-label="Push to talk"
        title="Hold to record voice input"
      >
        🎙
      </button>
      <div className="ptt-info">
        <div className={`ptt-status ${status !== 'idle' ? status : ''}`}>{statusText}</div>
        <div className="ptt-hint">
          {recording ? 'Release to send' : 'Hold the button and speak'}
        </div>
        {transcript && (
          <div className="ptt-transcript">"{transcript}"</div>
        )}
      </div>
    </div>
  );
}
