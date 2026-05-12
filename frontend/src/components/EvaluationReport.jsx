import React from 'react';
import styles from './EvaluationReport.module.css';

const EvaluationReport = ({ report, onRetry }) => {
    if (!report) return null;

    const {
        overall_score = 0,
        speech_agent = {},
        posture_agent = {},
        eye_contact_agent = {},
        emotion_agent = {},
        content_agent = {},
        feedback_good = [],
        feedback_improve = []
    } = report;

    const getScoreColor = (score) => {
        if (score >= 80) return '#10b981';
        if (score >= 50) return '#f59e0b';
        return '#ef4444';
    };

    const getScoreLabel = (score) => {
        if (score >= 80) return 'Excellent';
        if (score >= 50) return 'Good';
        return 'Needs Work';
    };

    const getStatusColor = (status) => {
        if (status === 'Good') return '#10b981';
        if (status === 'Fair') return '#f59e0b';
        return '#ef4444';
    };

    const StatRow = ({ label, value, color }) => (
        <div className={styles.statRow}>
            <span className={styles.statLabel}>{label}</span>
            <strong className={styles.statValue} style={{ color: color || '#f8fafc' }}>{value}</strong>
        </div>
    );

    const StatBlock = ({ label, value, color }) => (
        <div className={styles.statBlock}>
            <div className={styles.statLabel}>{label}</div>
            <div className={styles.statBlockValue} style={{ color: color || '#f8fafc' }}>{value}</div>
        </div>
    );

    const TagsBlock = ({ label, valueStr, issue = false }) => {
        if (!valueStr || valueStr === 'N/A' || valueStr === 'Good') {
            return <StatRow label={label} value="None" color="#10b981" />;
        }
        
        const capitalizeFirst = (str) => {
            if (!str) return str;
            return str.charAt(0).toUpperCase() + str.slice(1);
        };

        const tags = typeof valueStr === 'string' 
            ? valueStr.split('|').map(s => capitalizeFirst(s.trim())).filter(s => s) 
            : [capitalizeFirst(valueStr)];
            
        return (
            <div className={styles.statRow} style={{ alignItems: 'flex-start' }}>
                <div className={styles.statLabel}>{label}</div>
                <div className={styles.pillContainer} style={{ marginTop: '0', justifyContent: 'flex-end', maxWidth: '65%', textAlign: 'right' }}>
                    {tags.map((t, idx) => (
                        <span key={idx} className={styles.pill} style={{
                            backgroundColor: issue ? 'rgba(239, 68, 68, 0.1)' : 'rgba(56, 189, 248, 0.1)',
                            color: issue ? '#ef4444' : '#38bdf8',
                            borderColor: issue ? 'rgba(239, 68, 68, 0.25)' : 'rgba(56, 189, 248, 0.25)',
                            padding: '3px 8px',
                            fontSize: '0.75rem',
                            fontWeight: '500',
                        }}>{t}</span>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className={styles.container}>
            {/* ══════ HEADER ══════ */}
            <div className={styles.header}>
                <h2 className={styles.headerTitle}>Session Evaluation Report</h2>
                <p className={styles.headerSub}>Multi-agent analysis of your communication, reasoning, and delivery.</p>
            </div>

            {/* ══════ HERO SCORE BANNER ══════ */}
            <div className={styles.scoreBanner}>
                <div className={styles.scoreLeft}>
                    <div className={styles.scoreNumber}>{overall_score}</div>
                    <div>
                        <div className={styles.scoreLabel}>Overall Score</div>
                        <div className={styles.scoreBadge} style={{
                            backgroundColor: `${getScoreColor(overall_score)}20`,
                            color: getScoreColor(overall_score),
                        }}>
                            {getScoreLabel(overall_score)}
                        </div>
                    </div>
                </div>
                <div className={styles.scoreRight}>
                    <div className={styles.scoreMiniStat}>
                        <div className={styles.scoreMiniLabel}>Grammar</div>
                        <div className={styles.scoreMiniValue}>{content_agent.grammar || 0}%</div>
                    </div>
                    <div className={styles.scoreMiniStat}>
                        <div className={styles.scoreMiniLabel}>Posture</div>
                        <div className={styles.scoreMiniValue}>{posture_agent.score || 0}%</div>
                    </div>
                    <div className={styles.scoreMiniStat}>
                        <div className={styles.scoreMiniLabel}>Eye Contact</div>
                        <div className={styles.scoreMiniValue}>{eye_contact_agent.score || 0}%</div>
                    </div>
                    <div className={styles.scoreMiniStat}>
                        <div className={styles.scoreMiniLabel}>Fluency</div>
                        <div className={styles.scoreMiniValue}>{speech_agent.fluency || 0}%</div>
                    </div>
                </div>
            </div>

            {/* ══════ AGENT GRID: 3x1 ══════ */}
            <div className={styles.agentGrid}>
                {/* Speech Agent */}
                <div className={styles.agentCard}>
                    <div className={styles.agentHeader}>
                        <span className={styles.agentIcon}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" x2="12" y1="19" y2="22" /></svg>
                        </span>
                        <h3 className={styles.agentTitle}>Speech Analysis</h3>
                    </div>
                    <div className={styles.agentBody}>
                        <StatRow label="WPM" value={speech_agent.wpm || 'N/A'} />
                        <StatRow label="Fillers" value={speech_agent.fillers || '0'} />
                        <StatRow label="Fluency" value={`${speech_agent.fluency || '0'}%`} />
                    </div>
                </div>

                {/* Body Language & Eye Contact */}
                <div className={styles.agentCard}>
                    <div className={styles.agentHeader}>
                        <span className={styles.agentIcon}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                        </span>
                        <h3 className={styles.agentTitle}>Body Language</h3>
                    </div>
                    <div className={styles.agentBody}>
                        <StatRow label="Posture Score" value={`${posture_agent.score || 0}/100`} color={getStatusColor(posture_agent.status)} />
                        <StatRow label="Eye Contact Score" value={`${eye_contact_agent.score || 0}/100`} color={getStatusColor(eye_contact_agent.status)} />
                        <TagsBlock label="Observations" valueStr={eye_contact_agent.ai_observations} issue={true} />
                    </div>
                </div>

                {/* Content Agent — Enhanced */}
                <div className={styles.agentCard}>
                    <div className={styles.agentHeader}>
                        <span className={styles.agentIcon}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
                        </span>
                        <h3 className={styles.agentTitle}>Content & Delivery</h3>
                    </div>
                    <div className={styles.agentBody}>
                        <StatRow label="Grammar" value={`${content_agent.grammar || '0'}%`} color={getScoreColor(content_agent.grammar || 0)} />
                        <StatRow label="Relevance" value={`${content_agent.relevance || '0'}%`} color={getScoreColor(content_agent.relevance || 0)} />
                        {content_agent.keyword_coverage > 0 && (
                            <StatRow label="Keyword Coverage" value={`${content_agent.keyword_coverage || '0'}%`} color={getScoreColor(content_agent.keyword_coverage || 0)} />
                        )}
                        <TagsBlock label="Tone" valueStr={content_agent.tone} issue={false} />
                    </div>
                </div>
            </div>


            {/* ══════ FEEDBACK ROW ══════ */}
            <div className={styles.feedbackRow}>
                <div className={styles.feedbackCardGood}>
                    <div className={styles.feedbackHeader}>
                        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '20px', height: '20px' }}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                        </span>
                        <h3 className={styles.feedbackTitle}>Strengths</h3>
                    </div>
                    {feedback_good.length > 0 ? (
                        <div className={styles.feedbackList}>
                            {feedback_good.map((item, i) => (
                                <div key={i} className={styles.feedbackItem}>
                                    <span className={styles.feedbackNumGood}>{i + 1}</span>
                                    <span className={styles.feedbackText}>{item}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className={styles.emptyText}>No strengths recorded.</p>
                    )}
                </div>

                <div className={styles.feedbackCardImprove}>
                    <div className={styles.feedbackHeader}>
                        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '20px', height: '20px' }}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                        </span>
                        <h3 className={styles.feedbackTitle}>Areas for Improvement</h3>
                    </div>
                    {feedback_improve.length > 0 ? (
                        <div className={styles.feedbackList}>
                            {feedback_improve.map((item, i) => (
                                <div key={i} className={styles.feedbackItem}>
                                    <span className={styles.feedbackNumImprove}>{i + 1}</span>
                                    <span className={styles.feedbackText}>{item}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className={styles.emptyText}>Perfect — no improvements needed!</p>
                    )}
                </div>
            </div>

            {/* ══════ CTA ══════ */}
            <div className={styles.ctaContainer}>
                <button onClick={onRetry} className={styles.retryBtn}>
                    Start New Session
                </button>
            </div>
        </div>
    );
};

export default EvaluationReport;
