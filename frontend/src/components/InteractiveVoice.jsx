import { useState, useRef, useCallback, useEffect } from 'react';
import { speak } from '../api';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function InteractiveVoice({ onToast }) {
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState('idle'); // idle, listening, processing, speaking
  const [history, setHistory] = useState([]); // [{ role: 'user'|'agent', text: string }]

  const isActiveRef = useRef(isActive);
  useEffect(() => { isActiveRef.current = isActive; }, [isActive]);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const silenceTimerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const microphoneRef = useRef(null);
  const animationFrameRef = useRef(null);

  const stopAudioTracks = () => {
    if (microphoneRef.current) {
      microphoneRef.current.mediaStream.getTracks().forEach(t => t.stop());
    }
  };

  const startListening = useCallback(async () => {
    try {
      setStatus('listening');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      
      // Simple VAD via Web Audio API
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      microphoneRef.current = audioContextRef.current.createMediaStreamSource(stream);
      microphoneRef.current.connect(analyserRef.current);
      analyserRef.current.fftSize = 512;
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      let lastSpeechTime = Date.now();
      let isSpeakingNow = false;
      let hasSpoken = false;

      const detectSilence = () => {
        if (mr.state !== 'recording') return;
        analyserRef.current.getByteFrequencyData(dataArray);
        const sum = dataArray.reduce((a, b) => a + b, 0);
        const average = sum / bufferLength;

        if (average > 10) { // Threshold
          lastSpeechTime = Date.now();
          if (!isSpeakingNow) {
            isSpeakingNow = true;
            hasSpoken = true;
          }
        } else {
          if (isSpeakingNow && Date.now() - lastSpeechTime > 1500) {
            // Silence detected for 1.5s after speaking
            isSpeakingNow = false;
            mr.stop();
            return;
          }
        }
        animationFrameRef.current = requestAnimationFrame(detectSilence);
      };

      mr.onstart = () => detectSilence();

      mr.onstop = async () => {
        cancelAnimationFrame(animationFrameRef.current);
        stopAudioTracks();
        
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        if (!hasSpoken || blob.size < 1000) {
          // If the user never spoke or the file is too small, just loop silently
          if (isActiveRef.current) startListening();
          return;
        }
        
        setStatus('processing');
        
        // Send to voice command
        const form = new FormData();
        form.append('audio', blob, 'recording.webm');
        
        try {
          const res = await fetch(`${BASE}/api/voice/command`, { method: 'POST', body: form });
          if (!res.ok) throw new Error('Command failed');
          const data = await res.json();
          
          setHistory(prev => [...prev, { role: 'user', text: data.transcript }, { role: 'agent', text: data.spoken_summary }]);
          
          // Speak the result
          setStatus('speaking');
          const audioUrl = await speak(data.spoken_summary);
          if (audioUrl) {
            const audio = new Audio(audioUrl);
            audio.onended = () => {
              if (isActiveRef.current) startListening();
              else setStatus('idle');
            };
            audio.play();
          } else {
            // browser fallback
            const utt = new SpeechSynthesisUtterance(data.spoken_summary);
            utt.onend = () => {
              if (isActiveRef.current) startListening();
              else setStatus('idle');
            };
            speechSynthesis.speak(utt);
          }
        } catch (e) {
          onToast('Voice agent error', 'error');
          if (isActiveRef.current) startListening();
          else setStatus('idle');
        }
      };

      mr.start(100);
      mediaRecorderRef.current = mr;
      
      // Safety timeout in case no speech ever happens
      silenceTimerRef.current = setTimeout(() => {
        if (mr.state === 'recording' && !isSpeakingNow) {
          mr.stop();
        }
      }, 5000);

    } catch (e) {
      onToast('Microphone access denied', 'error');
      setIsActive(false);
      setStatus('idle');
    }
  }, [isActive, onToast]);

  const toggleActive = () => {
    setIsActive(!isActive);
  };

  useEffect(() => {
    if (isActive) {
      startListening();
    } else {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      stopAudioTracks();
      clearTimeout(silenceTimerRef.current);
      cancelAnimationFrame(animationFrameRef.current);
      setStatus('idle');
    }
    return () => {
      stopAudioTracks();
      clearTimeout(silenceTimerRef.current);
      cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isActive, startListening]);

  return (
    <div className="card fade-in" style={{ border: isActive ? '2px solid var(--primary)' : '1px solid var(--border)' }}>
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div className="card-title" style={{ margin: 0, color: 'var(--primary)', border: 'none', padding: 0 }}>🎙 Interactive Voice Agent</div>
          <p style={{ margin: 0, marginTop: '0.2rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Continuous conversation mode.</p>
        </div>
        <button 
          className={`btn ${isActive ? 'btn-danger' : 'btn-primary'}`}
          onClick={toggleActive}
        >
          {isActive ? 'Stop Listening' : 'Start Voice Mode'}
        </button>
      </div>

      {isActive && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: '#000', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ color: status === 'listening' ? 'var(--red)' : status === 'speaking' ? 'var(--green)' : 'var(--cyan)' }}>
            Status: <strong>{status.toUpperCase()}</strong>
          </div>
          
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '150px', overflowY: 'auto' }}>
            {history.map((msg, i) => (
              <div key={i} style={{ textAlign: msg.role === 'user' ? 'right' : 'left' }}>
                <span style={{ 
                  background: msg.role === 'user' ? 'rgba(0, 200, 220, 0.1)' : 'rgba(0, 255, 0, 0.1)',
                  color: msg.role === 'user' ? 'var(--cyan)' : 'var(--green)',
                  padding: '0.3rem 0.6rem',
                  borderRadius: 'var(--radius-sm)',
                  display: 'inline-block',
                  fontSize: '0.8rem'
                }}>
                  {msg.text}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
