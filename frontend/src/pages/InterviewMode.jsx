import React, { useState, useRef, useEffect, useCallback } from 'react';
import AudioRecorder from '../components/AudioRecorder';
import LivePostureTracker from '../components/LivePostureTracker';
import { useAuth } from '../context/AuthContext';
import EvaluationReport from '../components/EvaluationReport';
import { speakText } from '../utils/tts';
import { ENDPOINTS } from '../api/config';
import { authFetch } from '../api/authFetch';
import styles from './SessionMode.module.css';

const InterviewMode = () => {
    const { user } = useAuth();
    const roles = ["Data Analyst", "Full Stack Developer", "HR Manager", "Marketing Specialist", "Product Manager", "Software Engineer", "Software Tester"];
    const [jobRole, setJobRole] = useState(roles[0]);
    const [difficulty, setDifficulty] = useState("Medium");

    // Pre-fill from Orchestrator
    useEffect(() => {
        const prefilledRole = localStorage.getItem('orchestrator_role');
        if (prefilledRole) {
            const exists = roles.find(r => r.toLowerCase() === prefilledRole.toLowerCase());
            setJobRole(exists || prefilledRole);
            localStorage.removeItem('orchestrator_role');
        }
    }, []);

    const [isInterviewing, setIsInterviewing] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [chatHistory, setChatHistory] = useState([]);
    const [currentQuestion, setCurrentQuestion] = useState("");
    const [expectedKeywords, setExpectedKeywords] = useState("");
    const [idealAnswerSummary, setIdealAnswerSummary] = useState("");
    const [turnNumber, setTurnNumber] = useState(1);

    const [finalReport, setFinalReport] = useState(null);
    const [isFinished, setIsFinished] = useState(false);
    const [postureStats, setPostureStats] = useState({});

    const postureStatsRef = useRef(postureStats);
    postureStatsRef.current = postureStats;

    const [warningLevel, setWarningLevel] = useState(0);

    // 15-minute timer
    const [timeLeft, setTimeLeft] = useState(900);
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
        window.isSessionActive = isInterviewing;
        return () => { window.isSessionActive = false; };
    }, [isInterviewing]);

    const endInterview = useCallback(async (historyToSend) => {
        const history = historyToSend || chatHistoryRef.current;
        setIsProcessing(true);
        try {
            const formData = new FormData();
            formData.append("chat_history", JSON.stringify(history));
            formData.append("posture_stats", JSON.stringify(postureStatsRef.current));
            if (user?.id) formData.append("user_id", user.id);

            const res = await authFetch(ENDPOINTS.INTERVIEW_REPORT, { method: 'POST', body: formData });
            const report = await res.json();
            setFinalReport(report);
            setIsFinished(true);
            setIsInterviewing(false);
        } catch (e) {
            alert("Failed to generate report.");
        } finally {
            setIsProcessing(false);
        }
    }, [user]);

    // Timer logic
    useEffect(() => {
        if (isInterviewing && !isFinished) {
            timerRef.current = setInterval(() => {
                setTimeLeft((prev) => {
                    if (prev <= 1) {
                        clearInterval(timerRef.current);
                        endInterview();
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        } else {
            clearInterval(timerRef.current);
        }
        return () => clearInterval(timerRef.current);
    }, [isInterviewing, isFinished, endInterview]);

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    };

    const startSession = async () => {
        setChatHistory([]);
        setFinalReport(null);
        setIsFinished(false);
        setTurnNumber(1);
        setTimeLeft(900);
        setWarningLevel(0);
        setIsProcessing(false);

        try {
            const res = await authFetch(ENDPOINTS.INTERVIEW_START, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_role: jobRole, difficulty })
            });
            const data = await res.json();

            setCurrentQuestion(data.question);
            setExpectedKeywords(data.expected_keywords || "");
            setIdealAnswerSummary(data.ideal_answer_summary || "");

            setChatHistory([{ role: 'AI Judge', text: data.ai_greeting, logic_score: "" }]);
            speakText(data.ai_greeting);
            setIsInterviewing(true);
        } catch (e) {
            alert("Failed to start session. Backend running?");
        }
    };

    const handleAnswerUpload = (data) => {
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
                semantic_relevance: data.semantic_relevance || 0,
                expected_keywords: expectedKeywords || ''
            }
        ];

        if (data.next_question === "INTERVIEW_COMPLETE") {
            setChatHistory(newHistory);
            endInterview(newHistory);
        } else {
            newHistory.push({ role: 'AI Judge', text: data.next_question, logic_score: "" });
            setChatHistory(newHistory);
            setCurrentQuestion(data.next_question);
            speakText(data.next_question);
            setTurnNumber(prev => prev + 1);
        }
    };

    const handleRetry = () => {
        setIsFinished(false);
        setFinalReport(null);
        setIsInterviewing(false);
        setChatHistory([]);
        setPostureStats({});
        setWarningLevel(0);
        setTimeLeft(900);
        setTurnNumber(1);
        setIsProcessing(false);
        setCurrentQuestion("");
        setExpectedKeywords("");
        setIdealAnswerSummary("");
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2 className={styles.title}>Interview Practice</h2>
                {isInterviewing && (
                    <div className={styles.timer} style={{color: timeLeft < 60 ? '#ef4444' : '#10b981'}}>
                        {formatTime(timeLeft)}
                    </div>
                )}
            </div>

            {!isInterviewing && !isFinished ? (
                <div className={styles.startCard}>
                    <h3 className={styles.cardTitle} style={{ textAlign: 'center' }}>Configure Interview</h3>
                    <p className={styles.subtitle} style={{ textAlign: 'center' }}>
                        Select your job role and difficulty level to begin
                    </p>

                    <div className={styles.inputGroup}>
                        <label className={styles.inputLabel}>Job Role</label>
                        <select value={jobRole} onChange={e => setJobRole(e.target.value)} className={styles.select}>
                            {roles.map(r => <option key={r} value={r}>{r}</option>)}
                            {!roles.includes(jobRole) && <option key={jobRole} value={jobRole}>{jobRole} (Custom)</option>}
                        </select>
                    </div>

                    <div className={styles.inputGroup}>
                        <label className={styles.inputLabel}>Difficulty Level</label>
                        <select value={difficulty} onChange={e => setDifficulty(e.target.value)} className={styles.select}>
                            {["Easy", "Medium", "Hard"].map(d => <option key={d} value={d}>{d}</option>)}
                        </select>
                    </div>

                    <button onClick={startSession} className={styles.startBtn}>
                        Start Interview
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
                                isRecording={isInterviewing}
                                onMultiplePeopleWarning={(level) => setWarningLevel(level)}
                                onMultiplePeopleEnd={() => {
                                    alert("Session Ended: Multiple people detected in frame too many times.");
                                    endInterview();
                                }}
                            />
                        </div>
                        <div className={styles.controlsWrapper}>
                            <h4 className={styles.controlTitle}>Your Answer</h4>
                            <AudioRecorder
                                onUploadSuccess={handleAnswerUpload}
                                currentPostureStats={postureStats}
                                additionalFormData={{
                                    current_question: currentQuestion,
                                    chat_history: JSON.stringify(chatHistoryRef.current),
                                    expected_keywords: expectedKeywords,
                                    ideal_answer_summary: idealAnswerSummary,
                                    turn_number: String(turnNumber),
                                    job_role: jobRole
                                }}
                                uploadUrl={ENDPOINTS.INTERVIEW_REPLY}
                                onRecordStart={() => setIsProcessing(true)}
                                onRecordStop={() => { }}
                            />
                            <button onClick={() => endInterview()} className={styles.endBtn}>
                                End Interview Early
                            </button>
                        </div>
                    </div>

                    <div className={styles.chatBox}>
                        <div className={styles.chatHeader}>Live Interview</div>
                        <div className={styles.chatHistory}>
                            {chatHistory.map((msg, i) => (
                                <div key={i} className={styles.bubble} style={{animation: 'fadeInUp 0.3s ease-out forwards', alignSelf: msg.role === 'User' ? 'flex-end' : 'flex-start', backgroundColor: msg.role === 'User' ? '#0ea5e9' : '#1a1a1a', color: '#f8fafc'}}>
                                    <div className={styles.bubbleRole}>{msg.role === 'User' ? 'You' : 'Interviewer'}</div>
                                    <div className={styles.bubbleText}>{msg.text}</div>
                                </div>
                            ))}
                            {isProcessing && (
                                <div className={styles.bubble} style={{animation: 'fadeInUp 0.3s ease-out forwards', alignSelf: 'flex-start', backgroundColor: '#1a1a1a', color: '#94a3b8'}}>
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

export default InterviewMode;