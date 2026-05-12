import React, { useState, useEffect, useRef } from 'react';
import { ENDPOINTS } from '../api/config';
import { authFetch } from '../api/authFetch';

const AudioRecorder = ({
    onUploadSuccess,
    currentPostureStats = {},
    additionalFormData = {},
    onRecordStart,
    onRecordStop,
    uploadUrl = ENDPOINTS.INTRO_UPLOAD
}) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);

    const startRecording = async () => {
        setError(null);

        // Check if getUserMedia is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            const msg = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
                ? "Microphone access denied. Please allow microphone permissions in your browser."
                : "Microphone requires a secure connection. Please open http://localhost:3001 instead.";
            setError(msg);
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            audioChunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (event) => {
                audioChunksRef.current.push(event.data);
            };

            mediaRecorderRef.current.onstop = async () => {
                stream.getTracks().forEach(track => track.stop());
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                // We don't call uploadAudio directly here because it might use stale closure.
                // We'll use a ref to the latest posture stats or call a separate state updater.
                setPendingUpload(audioBlob);
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
            if (onRecordStart) onRecordStart();
        } catch (err) {
            console.error("Microphone error:", err);
            setError("Could not access microphone. Please check your browser permissions.");
        }
    };

    const latestPostureStats = useRef(currentPostureStats);
    useEffect(() => {
        latestPostureStats.current = currentPostureStats;
    }, [currentPostureStats]);

    const [pendingUpload, setPendingUpload] = useState(null);
    useEffect(() => {
        if (pendingUpload) {
            uploadAudio(pendingUpload);
            setPendingUpload(null);
        }
    }, [pendingUpload]);

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
        }
        setIsRecording(false);
        if (onRecordStop) onRecordStop();
    };

    const uploadAudio = async (blob) => {
        setIsUploading(true);
        const formData = new FormData();

        formData.append('audio_file', blob, 'recording.webm');
        formData.append('posture_data', JSON.stringify(latestPostureStats.current || currentPostureStats));

        Object.keys(additionalFormData).forEach(key => {
            formData.append(key, additionalFormData[key]);
        });

        try {
            const response = await authFetch(uploadUrl, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                onUploadSuccess(data);
            } else {
                const errText = await response.text();
                console.error("Upload failed:", response.status, errText);
                setError(`Upload failed (${response.status}). Please try again.`);
            }
        } catch (err) {
            console.error("Error uploading audio:", err);
            setError("Network error. Is the backend running?");
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div style={styles.container}>
            {error && (
                <div style={styles.errorBox}>{error}</div>
            )}
            <button
                onClick={isRecording ? stopRecording : startRecording}
                style={{
                    ...styles.btn,
                    background: isRecording
                        ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                        : 'linear-gradient(135deg, #38bdf8, #0ea5e9)',
                    boxShadow: isRecording
                        ? '0 0 15px rgba(239, 68, 68, 0.4)'
                        : '0 4px 15px rgba(56, 189, 248, 0.25)',
                    transform: isRecording ? 'scale(0.98)' : 'scale(1)',
                    color: isRecording ? '#ffffff' : '#000000',
                }}
                disabled={isUploading}
            >
                {isUploading ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }}>
                        Processing...
                    </span>
                ) : isRecording ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }}>
                        <span style={styles.recordDot}></span> Stop Recording
                    </span>
                ) : (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }}>
                        Start Recording
                    </span>
                )}
            </button>
        </div>
    );
};

const styles = {
    container: { textAlign: 'center', margin: '20px 0' },
    btn: {
        width: '100%',
        padding: '14px 28px', border: 'none', borderRadius: '12px',
        cursor: 'pointer', fontSize: '1rem', fontWeight: '700',
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        letterSpacing: '0.3px'
    },
    errorBox: {
        background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)',
        color: '#dc2626', padding: '12px 16px', borderRadius: '8px',
        fontSize: '0.85rem', marginBottom: '16px', lineHeight: '1.5',
    },
    recordDot: {
        width: '10px', height: '10px', backgroundColor: '#fff', borderRadius: '50%',
        animation: 'pulse 1.5s infinite', display: 'inline-block'
    }
};

export default AudioRecorder;