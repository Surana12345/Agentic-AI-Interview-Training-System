import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { ENDPOINTS } from '../api/config';
import { authFetch } from '../api/authFetch';
import styles from './Dashboard.module.css';

const SessionComparison = ({ history }) => {
    const [idx1, setIdx1] = useState(0);
    const [idx2, setIdx2] = useState(history.length - 1);

    const s1 = history[idx1];
    const s2 = history[idx2];

    const metrics = [
        { label: 'Confidence', key: 'score', icon: '💪', color1: '#ef4444', color2: '#10b981' },
        { label: 'Logic', key: 'logic', icon: '🧠', color1: '#f59e0b', color2: '#38bdf8' },
        { label: 'Eye Contact', key: 'eye', icon: '👁️', color1: '#8b5cf6', color2: '#a855f7' },
        { label: 'Posture', key: 'posture', icon: '🧍', color1: '#64748b', color2: '#94a3b8' },
    ];

    return (
        <div>
            <div className={styles.sessionComparisonGrid}>
                <div>
                    <label style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Earlier Session</label>
                    <input
                        type="range" min="0" max={history.length - 1} value={idx1}
                        onChange={(e) => setIdx1(parseInt(e.target.value))}
                        style={{ width: '100%', marginTop: '8px', accentColor: '#38bdf8' }}
                    />
                    <div style={{ textAlign: 'center', marginTop: '16px', padding: '16px', backgroundColor: '#111', borderRadius: '8px', border: '1px solid #1f2937' }}>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Earlier</div>
                        <div style={{ fontSize: '1rem', color: '#f8fafc', fontWeight: '600' }}>Session #{idx1 + 1}</div>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>{s1.name} - {s1.mode}</div>
                    </div>
                </div>
                <div>
                    <label style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Later Session</label>
                    <input
                        type="range" min="0" max={history.length - 1} value={idx2}
                        onChange={(e) => setIdx2(parseInt(e.target.value))}
                        style={{ width: '100%', marginTop: '8px', accentColor: '#38bdf8' }}
                    />
                    <div style={{ textAlign: 'center', marginTop: '16px', padding: '16px', backgroundColor: '#111', borderRadius: '8px', border: '1px solid #1f2937' }}>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Later</div>
                        <div style={{ fontSize: '1rem', color: '#f8fafc', fontWeight: '600' }}>Session #{idx2 + 1}</div>
                        <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '4px' }}>{s2.name} - {s2.mode}</div>
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {metrics.map(m => {
                    const v1 = s1[m.key] || 0;
                    const v2 = s2[m.key] || 0;
                    const diff = v2 - v1;
                    const diffStr = diff > 0 ? `+${diff}` : diff;
                    const diffColor = diff > 0 ? '#10b981' : diff < 0 ? '#ef4444' : '#64748b';

                    return (
                        <div key={m.label} style={{ display: 'grid', gridTemplateColumns: '1fr 60px 1fr', gap: '20px', alignItems: 'center' }}>
                            <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                                    <span style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>{m.icon} {m.label}</span>
                                    <span style={{ fontSize: '0.9rem', color: m.color1, fontWeight: '600' }}>{v1}</span>
                                </div>
                                <div style={{ width: '100%', backgroundColor: '#1f2937', height: '4px', borderRadius: '2px' }}>
                                    <div style={{ width: `${v1}%`, backgroundColor: m.color1, height: '100%', borderRadius: '2px' }}></div>
                                </div>
                            </div>

                            <div style={{ textAlign: 'center', fontSize: '0.85rem', fontWeight: '700', color: diffColor }}>
                                {diffStr}
                            </div>

                            <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                                    <span style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>{m.icon} {m.label}</span>
                                    <span style={{ fontSize: '0.9rem', color: m.color2, fontWeight: '600' }}>{v2}</span>
                                </div>
                                <div style={{ width: '100%', backgroundColor: '#1f2937', height: '4px', borderRadius: '2px' }}>
                                    <div style={{ width: `${v2}%`, backgroundColor: m.color2, height: '100%', borderRadius: '2px' }}></div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

const Dashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState(null);
    const [filter, setFilter] = useState("All");
    const [timeFilter, setTimeFilter] = useState("All");
    const [loading, setLoading] = useState(true);
    const [orchestratorPrompt, setOrchestratorPrompt] = useState("");
    const [orchestratorReply, setOrchestratorReply] = useState("");
    const [isRouting, setIsRouting] = useState(false);

    const handleSmartStart = async (e) => {
        e.preventDefault();
        if (!orchestratorPrompt.trim()) return;

        setIsRouting(true);
        setOrchestratorReply(""); // clear previous
        try {
            const res = await authFetch(ENDPOINTS.ORCHESTRATOR_REQUEST, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: orchestratorPrompt })
            });

            if (res.status === 401) {
                alert("Session expired. Please log in again.");
                navigate("/login");
                return;
            }

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                alert(errData.detail || `Server error: ${res.status}`);
                return;
            }

            const data = await res.json();

            if (data.status === "success") {
                const decision = data.data;

                if (decision.routed_module === "interview" && decision.extracted_job_role) {
                    const role = decision.extracted_job_role;
                    const allowedRoles = ["Data Analyst", "Full Stack Developer", "HR Manager", "Marketing Specialist", "Product Manager", "Software Engineer", "Software Tester"];
                    const isAllowed = allowedRoles.some(r => r.toLowerCase() === role.toLowerCase());

                    if (!isAllowed) {
                        setOrchestratorReply(`We don't specialize in a "${role}" role yet. Available roles are: ${allowedRoles.join(', ')}. Please select one of these!`);
                        return; // Halt routing
                    }
                }

                setOrchestratorReply(decision.sys_reply);

                if (decision.extracted_job_role) {
                    localStorage.setItem('orchestrator_role', decision.extracted_job_role);
                }
                if (decision.extracted_topic) {
                    localStorage.setItem('orchestrator_topic', decision.extracted_topic);
                }

                setTimeout(() => {
                    if (decision.routed_module === "interview") navigate("/interview");
                    else if (decision.routed_module === "debate") navigate("/debate");
                    else if (decision.routed_module === "intro") navigate("/intro");
                }, 2200);
            }
        } catch (err) {
            console.error("Orchestrator error:", err);
            alert("Failed to reach the backend. Make sure the server is running.");
        } finally {
            setIsRouting(false);
            setOrchestratorPrompt("");
        }
    };

    useEffect(() => {
        setLoading(true);
        authFetch(ENDPOINTS.DASHBOARD_STATS)
            .then(res => {
                if (!res.ok) throw new Error(`Server error: ${res.status}`);
                return res.json();
            })
            .then(data => {
                if (data.history) {
                    const formatSessionDate = (name) => {
                        if (!name) return '';
                        const parts = name.split(' ');
                        const datePart = parts[0];
                        if (datePart.includes('-')) {
                            const [yyyy, mm, dd] = datePart.split('-');
                            if (yyyy && mm && dd && yyyy.length === 4) {
                                return parts.length > 1 ? `${dd}/${mm}/${yyyy} ${parts.slice(1).join(' ')}` : `${dd}/${mm}/${yyyy}`;
                            }
                        }
                        return name;
                    };
                    data.history = data.history.map(s => ({ ...s, name: formatSessionDate(s.name) }));
                }
                setStats(data); setLoading(false);
            })
            .catch(err => { console.error("Error loading stats:", err); setLoading(false); });
    }, [user]);

    if (loading) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#6b7280', fontSize: '0.95rem' }}>
                Loading your performance data...
            </div>
        );
    }

    if (!stats) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', color: '#6b7280', fontSize: '0.95rem' }}>
                Unable to load dashboard data. Make sure the backend is running.
            </div>
        );
    }

    const hasData = stats.history && stats.history.length > 0;

    // Filter logic
    const parseDate = (dateStr) => {
        try {
            if (!dateStr) return new Date();
            const parts = dateStr.split(' ');
            if (parts[0] && parts[0].includes('/')) {
                const [day, month, year] = parts[0].split('/');
                return new Date(`${year}-${month}-${day}T${parts[1] || '00:00:00'}`);
            }
        } catch (e) { }
        return new Date();
    };

    const now = new Date();
    let timeLimit = null;
    if (timeFilter === "1D") timeLimit = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    else if (timeFilter === "1W") timeLimit = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    else if (timeFilter === "1M") timeLimit = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const filteredHistory = stats.history.filter(s => {
        const modeMatch = filter === "All" || s.mode === filter;
        let timeMatch = true;
        if (timeLimit) {
            const rowDate = parseDate(s.name);
            timeMatch = rowDate >= timeLimit;
        }
        return modeMatch && timeMatch;
    });

    // Custom Tooltip for Line Chart
    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const d = payload[0].payload;
            return (
                <div className={styles.tooltip}>
                    <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>{d.name}</p>
                    <p style={{ margin: '4px 0 0', fontWeight: '600', color: '#f8fafc' }}>Score: {d.score}%</p>
                    <p style={{ margin: '2px 0 0', fontSize: '0.78rem', color: '#38bdf8' }}>{d.mode}</p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className={styles.container}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 className={styles.greeting}>Welcome back, {user?.name || 'User'}</h1>
            </div>

            {/* ORCHESTRATOR SMART BAR */}
            <div className={styles.card} style={{ marginBottom: '24px', background: 'linear-gradient(145deg, #0a0a0a, #111827)', border: '1px solid #38bdf840' }}>
                <h3 className={styles.cardTitle} style={{ color: '#38bdf8', marginBottom: '12px' }}>✨ Smart Start</h3>
                <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '16px' }}>Tell the AI what you want to practice, and it will configure the right environment automatically.</p>
                <form onSubmit={handleSmartStart} style={{ display: 'flex', gap: '10px' }}>
                    <input
                        type="text"
                        value={orchestratorPrompt}
                        onChange={(e) => setOrchestratorPrompt(e.target.value)}
                        placeholder="e.g. 'I have a Software Engineer interview tomorrow' or 'Let's debate about remote work'"
                        disabled={isRouting}
                        style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid #334155', background: '#000', color: '#fff', fontSize: '0.95rem' }}
                    />
                    <button
                        type="submit"
                        disabled={isRouting || !orchestratorPrompt.trim()}
                        style={{ padding: '0 24px', borderRadius: '8px', background: '#38bdf8', color: '#000', fontWeight: 'bold', border: 'none', cursor: isRouting ? 'not-allowed' : 'pointer', opacity: isRouting ? 0.7 : 1 }}
                    >
                        {isRouting ? 'Routing...' : 'Go'}
                    </button>
                </form>
                {orchestratorReply && (
                    <div style={{ marginTop: '16px', padding: '12px 16px', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', borderRadius: '8px', border: '1px solid rgba(56, 189, 248, 0.2)', fontSize: '0.9rem', animation: 'fadeInUp 0.3s ease-out' }}>
                        💡 {orchestratorReply}
                    </div>
                )}
            </div>

            {/* Summary Cards */}
            <div className={styles.summaryRow}>
                <div className={styles.summaryCard}>
                    <div className={styles.summaryValue}>{stats.total_sessions || 0}</div>
                    <div className={styles.summaryLabel}>Total Sessions</div>
                </div>
                <div className={styles.summaryCard}>
                    <div className={styles.summaryValue}>{stats.avg_score || 0}%</div>
                    <div className={styles.summaryLabel}>Average Score</div>
                </div>
                <div className={styles.summaryCard}>
                    <div className={styles.summaryValue}>{stats.sessions_by_mode?.Intro || 0}</div>
                    <div className={styles.summaryLabel}>Intro Sessions</div>
                </div>
                <div className={styles.summaryCard}>
                    <div className={styles.summaryValue}>{stats.sessions_by_mode?.Debate || 0}</div>
                    <div className={styles.summaryLabel}>Debate Sessions</div>
                </div>
                <div className={styles.summaryCard}>
                    <div className={styles.summaryValue}>{stats.sessions_by_mode?.Interview || 0}</div>
                    <div className={styles.summaryLabel}>Interview Sessions</div>
                </div>
            </div>

            {!hasData ? (
                <div className={styles.card} style={{ textAlign: 'center', padding: '60px 40px' }}>
                    <h3 style={{ color: '#f8fafc', marginBottom: '8px' }}>No sessions yet</h3>
                    <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
                        Complete your first Intro, Debate, or Interview session to see your performance data.
                    </p>
                </div>
            ) : (
                <>
                    <div className={styles.mainGrid}>
                        {/* RADAR CHART */}
                        <div className={styles.card}>
                            <h3 className={styles.cardTitle}>Skill Assessment</h3>
                            <div style={{ display: 'flex', gap: '16px', marginBottom: '8px', justifyContent: 'center' }}>
                                <span style={{ fontSize: '0.75rem', color: '#38bdf8' }}>● Latest Session</span>
                                <span style={{ fontSize: '0.75rem', color: '#a855f7' }}>● All-time Average</span>
                            </div>
                            <div style={{ width: '100%', height: 320 }}>
                                <ResponsiveContainer>
                                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={stats.radar}>
                                        <PolarGrid stroke="#334155" />
                                        <PolarAngleAxis
                                            dataKey="subject"
                                            tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 500 }}
                                        />
                                        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                                        <Radar
                                            name="Latest"
                                            dataKey="latest"
                                            stroke="#38bdf8"
                                            fill="#38bdf8"
                                            fillOpacity={0.35}
                                        />
                                        <Radar
                                            name="Average"
                                            dataKey="avg"
                                            stroke="#a855f7"
                                            fill="#a855f7"
                                            fillOpacity={0.2}
                                        />
                                        <Tooltip contentStyle={{ borderRadius: '10px', border: '1px solid #1f2937', backgroundColor: '#0a0a0a', color: '#f8fafc', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }} />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        <div className={styles.rightColumn}>
                            {/* QUICK STATS & FILTER */}
                            <div className={styles.card}>
                                <h3 className={styles.cardTitle}>Latest Session</h3>
                                <div className={styles.statLine}>
                                    <span style={{ color: '#6b7280', fontSize: '0.9rem' }}>
                                        {stats.latest_mode} Mode
                                    </span>
                                    <strong style={{
                                        color: stats.latest_score >= 80 ? '#10b981' : stats.latest_score >= 50 ? '#f59e0b' : '#ef4444',
                                        fontSize: '1.4rem'
                                    }}>
                                        {stats.latest_score}/100
                                    </strong>
                                </div>
                                <div style={{ marginTop: '16px' }}>
                                    <label className={styles.filterLabel}>Filter by Mode</label>
                                    <select value={filter} onChange={(e) => setFilter(e.target.value)} className={styles.select}>
                                        <option value="All">All Modes</option>
                                        <option value="Intro">Intro Mode</option>
                                        <option value="Debate">Debate Mode</option>
                                        <option value="Interview">Interview Mode</option>
                                    </select>
                                </div>
                            </div>

                            {/* LINE CHART */}
                            <div className={styles.card} style={{ flexGrow: 1 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                    <h3 className={styles.cardTitle} style={{ margin: 0 }}>Progress Timeline</h3>
                                    <div style={{ display: 'flex', gap: '4px', background: '#050505', padding: '4px', borderRadius: '8px', border: '1px solid #1e293b' }}>
                                        {['1D', '1W', '1M', 'All'].map(t => (
                                            <button
                                                key={t}
                                                onClick={() => setTimeFilter(t)}
                                                style={{
                                                    padding: '4px 12px',
                                                    borderRadius: '6px',
                                                    border: 'none',
                                                    background: timeFilter === t ? '#38bdf8' : 'transparent',
                                                    color: timeFilter === t ? '#000' : '#94a3b8',
                                                    fontSize: '0.8rem',
                                                    cursor: 'pointer',
                                                    fontWeight: timeFilter === t ? '600' : '500',
                                                    transition: 'all 0.2s ease'
                                                }}
                                            >
                                                {t}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div style={{ width: '100%', height: 200 }}>
                                    <ResponsiveContainer>
                                        <LineChart data={filteredHistory}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f2937" />
                                            <XAxis
                                                dataKey="name"
                                                tick={false}
                                                axisLine={{ stroke: '#1f2937' }}
                                                tickLine={false}
                                            />
                                            <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                                            <Tooltip content={<CustomTooltip />} />
                                            <Line
                                                type="monotone"
                                                dataKey="score"
                                                stroke="#38bdf8"
                                                strokeWidth={2.5}
                                                dot={{ r: 4, stroke: '#0a0a0a', strokeWidth: 2, fill: '#38bdf8' }}
                                                activeDot={{ r: 6, fill: '#7dd3fc', stroke: '#0a0a0a', strokeWidth: 2 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* SESSION COMPARISON */}
                    {hasData && stats.history.length >= 2 && (
                        <div className={styles.card} style={{ marginTop: '20px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                <span style={{ fontSize: '1.2rem' }}>🔀</span>
                                <h3 className={styles.cardTitle}>Session Comparison</h3>
                            </div>
                            <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '24px' }}>Drag the sliders to compare any two sessions side-by-side</p>

                            <SessionComparison history={stats.history} />
                        </div>
                    )}

                    {/* RECENT ACTIVITY TABLE */}
                    <div className={styles.card} style={{ marginTop: '20px' }}>
                        <h3 className={styles.cardTitle}>Recent Activity</h3>
                        {filteredHistory.length === 0 ? (
                            <p style={{ color: '#9ca3af', fontSize: '0.9rem', textAlign: 'center', padding: '20px' }}>
                                No sessions found for this filter.
                            </p>
                        ) : (
                            <div style={{ overflowX: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                                    <thead>
                                        <tr style={{ borderBottom: '2px solid #1f2937' }}>
                                            <th className={styles.th}>Date</th>
                                            <th className={styles.th}>Mode</th>
                                            <th className={styles.th}>Score</th>
                                            <th className={styles.th}>Logic</th>
                                            <th className={styles.th}>Eye Contact</th>
                                            <th className={styles.th}>Posture</th>
                                            <th className={styles.th}>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredHistory.slice().reverse().map((session, index) => (
                                            <tr key={index} style={{ borderBottom: '1px solid #1a1a1a' }}>
                                                <td className={styles.td}>{session.name}</td>
                                                <td className={styles.td}>
                                                    <span className={styles.modeBadge} style={{
                                                        backgroundColor: session.mode === 'Interview' ? 'rgba(56, 189, 248, 0.2)' : session.mode === 'Debate' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                                                        color: session.mode === 'Interview' ? '#38bdf8' : session.mode === 'Debate' ? '#fbbf24' : '#34d399'
                                                    }}>
                                                        {session.mode}
                                                    </span>
                                                </td>
                                                <td className={styles.td} style={{ fontWeight: '600', color: '#f8fafc' }}>{session.score}%</td>
                                                <td className={styles.td}>{session.logic || 0}%</td>
                                                <td className={styles.td}>{session.eye || 0}%</td>
                                                <td className={styles.td}>{session.posture || 0}%</td>
                                                <td className={styles.td}>
                                                    <span style={{
                                                        color: session.score >= 80 ? '#10b981' : session.score >= 50 ? '#f59e0b' : '#ef4444',
                                                        fontSize: '0.85rem', fontWeight: '500'
                                                    }}>
                                                        {session.score >= 80 ? 'Excellent' : session.score >= 50 ? 'Good' : 'Needs Work'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default Dashboard;