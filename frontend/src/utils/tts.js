import { ENDPOINTS } from '../api/config';
import { authFetch } from '../api/authFetch';

/**
 * Speak text using backend TTS (gTTS) with fallback to browser SpeechSynthesis.
 * The backend returns base64-encoded MP3 audio for natural-sounding speech.
 */
export const speakText = async (text) => {
    if (!text || !text.trim()) return;

    // 1. Try backend TTS first (natural voice)
    try {
        const res = await authFetch(ENDPOINTS.TTS_SYNTHESIZE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await res.json();

        if (data.audio_base64) {
            const audioBytes = Uint8Array.from(
                atob(data.audio_base64),
                c => c.charCodeAt(0)
            );
            const blob = new Blob([audioBytes], { type: data.mime_type || 'audio/mp3' });
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            audio.volume = 1.0;           // Max volume
            audio.playbackRate = 1.25;    // Slightly faster playback
            audio.onended = () => URL.revokeObjectURL(url);
            await audio.play();
            return;
        }
    } catch (e) {
        console.warn('Backend TTS failed, falling back to browser:', e);
    }

    // 2. Fallback to browser SpeechSynthesis
    if (!('speechSynthesis' in window)) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);

    const setVoice = () => {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length === 0) return;

        const preferred = voices.find(v =>
            v.name.includes('Female') ||
            v.name.includes('Zira') ||
            v.name.includes('Samantha') ||
            v.name.includes('Victoria') ||
            v.name.toLowerCase().includes('woman')
        );

        if (preferred) utterance.voice = preferred;
        utterance.rate = 1.3;    // Faster speech
        utterance.pitch = 1.1;
        utterance.volume = 1.0;  // Max volume
        window.speechSynthesis.speak(utterance);
    };

    if (window.speechSynthesis.getVoices().length === 0) {
        window.speechSynthesis.addEventListener('voiceschanged', setVoice, { once: true });
    } else {
        setVoice();
    }
};
