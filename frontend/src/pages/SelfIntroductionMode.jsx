import React, { useState, useEffect } from 'react';
import AudioRecorder from '../components/AudioRecorder';
import LivePostureTracker from '../components/LivePostureTracker';
import { useAuth } from '../context/AuthContext';
import EvaluationReport from '../components/EvaluationReport';
import styles from './SessionMode.module.css';

const SelfIntroductionMode = () => {
    const { user } = useAuth();
    const [results, setResults] = useState(null);
    const [postureStats, setPostureStats] = useState({});
    const [isRecording, setIsRecording] = useState(false);

    useEffect(() => {
        window.isSessionActive = !results && isRecording;
        return () => { window.isSessionActive = false; };
    }, [results, isRecording]);

    const handleRetry = () => {
        setResults(null);
        setIsRecording(false);
        setPostureStats({});
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2 className={styles.title}>Self-Introduction Practice</h2>
            </div>

            {results ? (
                <EvaluationReport report={results} onRetry={handleRetry} />
            ) : (
                <div className={styles.activeGrid}>
                    <div className={styles.sidebar}>
                        <div className={styles.trackerWrapper}>
                            <LivePostureTracker
                                onStatsUpdate={(stats) => setPostureStats(stats)}
                                isRecording={isRecording}
                            />
                        </div>
                    </div>

                    <div className={styles.controlsWrapper}>
                        <h3 className={styles.cardTitle}>Record Your Intro</h3>
                        <p className={styles.subtitle}>Practice your 30-second elevator pitch. Speak clearly and maintain good posture.</p>

                        <div className={styles.recorderContainer}>
                            <AudioRecorder
                                onUploadSuccess={(data) => setResults(data)}
                                currentPostureStats={postureStats}
                                onRecordStart={() => setIsRecording(true)}
                                onRecordStop={() => setIsRecording(false)}
                                additionalFormData={user?.id ? { user_id: String(user.id) } : {}}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SelfIntroductionMode;