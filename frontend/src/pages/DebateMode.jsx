import React, { useState, useRef, useEffect, useCallback } from 'react';
import AudioRecorder from '../components/AudioRecorder';
import LivePostureTracker from '../components/LivePostureTracker';
import { useAuth } from '../context/AuthContext';
import EvaluationReport from '../components/EvaluationReport';
import { ENDPOINTS } from '../api/config';
import { authFetch } from '../api/authFetch';
import { speakText } from '../utils/tts';
import styles from './SessionMode.module.css';

const DebateMode = () => {
    const { user } = useAuth();
    const [topic, setTopic] = useState("");
    const [customInput, setCustomInput] = useState("");

    useEffect(() => {
        const prefilledTopic = localStorage.getItem('orchestrator_topic');
        if (prefilledTopic) {
            setCustomInput(prefilledTopic);
            localStorage.removeItem('orchestrator_topic');
        }
    }, []);

    const [isDebating, setIsDebating] = useState(false);
    const [chatHistory, setChatHistory] = useState([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [finalReport, setFinalReport] = useState(null);
    const [isFinished, setIsFinished] = useState(false);
    const [postureStats, setPostureStats] = useState({});

    const postureStatsRef = useRef(postureStats);
    postureStatsRef.current = postureStats;

    const [warningLevel, setWarningLevel] = useState(0);

    // 15-minute timer state
    const [timeLeft, setTimeLeft] = useState(900); // 15 mins in seconds
    const timerRef = useRef(null);

    const chatEndRef = useRef(null);
    const chatHistoryRef = useRef(chatHistory);
    chatHistoryRef.current = chatHistory;

    useEffect(() => {
        if (chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [chatHistory]);

    // Set session active flag for nav guard
    useEffect(() => {
        window.isSessionActive = isDebating;
        return () => { window.isSessionActive = false; };
    }, [isDebating]);

    const endDebate = useCallback(async (historyToSend) => {
        const history = historyToSend || chatHistoryRef.current;
        setIsProcessing(true);
        try {
            const formData = new FormData();
            formData.append("chat_history", JSON.stringify(history));
            formData.append("posture_stats", JSON.stringify(postureStatsRef.current));

            if (user?.id) formData.append("user_id", user.id);
            const res = await authFetch(ENDPOINTS.DEBATE_REPORT, { method: 'POST', body: formData });
            const report = await res.json();
            setFinalReport(report);
            setIsFinished(true);
            setIsDebating(false);
        } catch (e) {
            alert("Report failed!");
        } finally {
            setIsProcessing(false);
        }
    }, [user]);

    // Timer logic
    useEffect(() => {
        if (isDebating && !isFinished) {
            timerRef.current = setInterval(() => {
                setTimeLeft((prev) => {
                    if (prev <= 1) {
                        clearInterval(timerRef.current);
                        endDebate();
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        } else {
            clearInterval(timerRef.current);
        }
        return () => clearInterval(timerRef.current);
    }, [isDebating, isFinished, endDebate]);

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    const startDebate = async () => {
        setChatHistory([]);
        setFinalReport(null);
        setIsFinished(false);
        setTimeLeft(900);
        setWarningLevel(0);
        setIsProcessing(false);

        try {
            const res = await authFetch(ENDPOINTS.DEBATE_START, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: customInput })
            });
            const data = await res.json();
            setTopic(data.topic);
            const aiText = `Debate Topic: ${data.topic}. Please start your argument.`;
            setChatHistory([{ role: 'AI', text: aiText, logic_score: "" }]);
            speakText(aiText);
            setIsDebating(true);
        } catch (e) {
            alert("Failed to start debate. Backend running?");
        }
    };

    const handleSpeechUpload = (data) => {
        setIsProcessing(false);
        const newHistory = [
            ...chatHistoryRef.current,
            {
                role: 'User',
                text: data.user_transcript,
                logic_score: data.logic_score,
                wpm: data.wpm || 0,
                fillers: data.fillers || 0,
                fluency: data.fluency || 0,
                emotion: data.emotion || 'neutral',
                semantic_relevance: data.semantic_relevance || 0
            },
            { role: 'AI', text: data.ai_counter_argument, logic_score: "" }
        ];
        setChatHistory(newHistory);
        speakText(data.ai_counter_argument);
    };

    const handleRetry = () => {
        setIsFinished(false);
        setFinalReport(null);
        setIsDebating(false);
        setChatHistory([]);
        setPostureStats({});
        setWarningLevel(0);
        setTimeLeft(900);
        setIsProcessing(false);
        setTopic("");
        setCustomInput("");
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2 className={styles.title}>Debate Practice</h2>
                {isDebating && (
                    <div className={styles.timer} style={{ color: timeLeft < 60 ? '#ef4444' : '#10b981' }}>
                        {formatTime(timeLeft)}
                    </div>
                )}
            </div>

            {!isDebating && !isFinished ? (
                <div className={styles.startCard}>
                    <h3 className={styles.cardTitle} style={{ textAlign: 'center' }}>Configure Your Debate</h3>
                    <p className={styles.subtitle} style={{ textAlign: 'center' }}>
                        Enter a statement to argue about, or leave blank for a random topic
                    </p>
                    <div className={styles.inputGroup}>
                        <label className={styles.inputLabel}>Debate Topic (Optional)</label>
                        <input
                            type="text"
                            placeholder="e.g., Remote work is worse for productivity"
                            value={customInput}
                            onChange={e => setCustomInput(e.target.value)}
                            className={styles.input}
                        />
                    </div>
                    <button onClick={startDebate} className={styles.startBtn}>
                        Start Debate Session
                    </button>
                </div>
            ) : isFinished && finalReport ? (
                <EvaluationReport report={finalReport} onRetry={handleRetry} />
            ) : (
                <div className={styles.activeGrid}>
                    <div className={styles.sidebar}>
                        <div className={styles.trackerWrapper}>
                            {warningLevel > 0 && (
                                <div style={{ backgroundColor: '#b91c1c', color: 'white', padding: '10px', textAlign: 'center', fontWeight: 'bold' }}>
                                    WARNING: MULTIPLE PEOPLE DETECTED ({warningLevel}/3)
                                </div>
                            )}
                            <LivePostureTracker
                                onStatsUpdate={setPostureStats}
                                isRecording={isDebating}
                                onMultiplePeopleWarning={(level) => setWarningLevel(level)}
                                onMultiplePeopleEnd={() => {
                                    alert("Session Ended: Multiple people detected in frame too many times.");
                                    endDebate();
                                }}
                            />
                        </div>
                        <div className={styles.controlsWrapper}>
                            <h4 className={styles.controlTitle}>Your Rebuttal</h4>
                            <AudioRecorder
                                onUploadSuccess={handleSpeechUpload}
                                currentPostureStats={postureStats}
                                additionalFormData={{
                                    topic: topic,
                                    chat_history: JSON.stringify(chatHistoryRef.current)
                                }}
                                uploadUrl={ENDPOINTS.DEBATE_REPLY}
                                onRecordStart={() => setIsProcessing(true)}
                                onRecordStop={() => { }}
                            />
                            <button onClick={() => endDebate()} className={styles.endBtn}>
                                End Session & Get Report
                            </button>
                        </div>
                    </div>

                    <div className={styles.chatBox}>
                        <div className={styles.chatHeader}>Live Debate</div>
                        <div className={styles.chatHistory}>
                            {chatHistory.map((msg, i) => (
                                <div key={i} className={styles.bubble} style={{ animation: 'fadeInUp 0.3s ease-out forwards', alignSelf: msg.role === 'User' ? 'flex-end' : 'flex-start', backgroundColor: msg.role === 'User' ? '#0ea5e9' : '#1a1a1a', color: '#f8fafc' }}>
                                    <div className={styles.bubbleRole}>{msg.role === 'User' ? 'You' : 'Opponent'}</div>
                                    <div className={styles.bubbleText}>{msg.text}</div>
                                </div>
                            ))}
                            {isProcessing && (
                                <div className={styles.bubble} style={{ animation: 'fadeInUp 0.3s ease-out forwards', alignSelf: 'flex-start', backgroundColor: '#1a1a1a', color: '#94a3b8' }}>
                                    <div className={styles.bubbleText}>Processing...</div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DebateMode;