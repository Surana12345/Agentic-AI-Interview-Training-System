import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import SelfIntroductionMode from './pages/SelfIntroductionMode';
import DebateMode from './pages/DebateMode';
import InterviewMode from './pages/InterviewMode';

// Simple 404
const NotFound = () => (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8' }}>
        <h2 style={{ fontSize: '3rem', margin: 0, color: '#38bdf8' }}>404</h2>
        <p>Page not found</p>
        <Link to="/" style={{ color: '#0ea5e9', textDecoration: 'none', marginTop: '10px' }}>Return Home</Link>
    </div>
);

// Protected route wrapper
const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();
    if (loading) {
        return (
            <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                height: '100vh', width: '100vw',
                background: '#000000',
                color: '#38bdf8', fontSize: '1rem', fontFamily: "'Inter', sans-serif",
            }}>
                <div style={{ textAlign: 'center', animation: 'pulse 1.5s infinite ease-in-out' }}>
                    <div style={{ fontSize: '0.9rem', opacity: 0.7 }}>Loading your session...</div>
                </div>
            </div>
        );
    }
    return user ? children : <Navigate to="/login" replace />;
};

// Sidebar nav link with active state
const NavLink = ({ to, label, icon }) => {
    const location = useLocation();
    const isActive = location.pathname === to;

    const blockSwitch = (e) => {
        if (!isActive && window.isSessionActive) {
            const leave = window.confirm("⚠️ You have an active session running. Are you sure you want to exit and lose progress?");
            if (!leave) {
                e.preventDefault();
            }
        }
    };

    return (
        <Link
            to={to}
            onClick={blockSwitch}
            style={{
                ...styles.link,
                background: isActive ? 'linear-gradient(90deg, rgba(56, 189, 248, 0.12) 0%, transparent 100%)' : 'transparent',
                color: isActive ? '#38bdf8' : '#94a3b8',
                fontWeight: isActive ? '600' : '400',
                borderLeft: isActive ? '3px solid #38bdf8' : '3px solid transparent',
            }}
        >
            {label}
        </Link>
    );
};

// Main layout with sidebar
const AppLayout = () => {
    const { user, logout } = useAuth();
    const location = useLocation();

    return (
        <div style={styles.layout}>
            <nav style={styles.sidebar}>
                <div style={styles.brand}>AI Interview<br /><span style={{ fontSize: '0.9rem', color: '#94a3b8', fontWeight: '500' }}>Training System</span></div>

                {/* User card */}
                <div style={styles.userCard}>
                    <div style={styles.userAvatar}>
                        {user?.name?.charAt(0)?.toUpperCase() || '?'}
                    </div>
                    <div style={styles.userInfo}>
                        <div style={styles.userName}>{user?.name || 'User'}</div>
                        <div style={styles.userEmail}>{user?.email || ''}</div>
                    </div>
                </div>

                <div style={styles.links}>
                    <NavLink to="/" label="Dashboard" />
                    <NavLink to="/intro" label="Intro Mode" />
                    <NavLink to="/debate" label="Debate Mode" />
                    <NavLink to="/interview" label="Interview Mode" />
                </div>

                <div style={styles.sidebarBottom}>
                    <button
                        id="btn-logout"
                        onClick={logout}
                        style={styles.logoutBtn}
                        onMouseOver={(e) => { e.target.style.background = 'rgba(239, 68, 68, 0.1)'; e.target.style.color = '#fca5a5'; }}
                        onMouseOut={(e) => { e.target.style.background = 'transparent'; e.target.style.color = '#f87171'; }}
                    >
                        Sign Out
                    </button>
                </div>
            </nav>

            <main style={styles.main}>
                <div key={location.pathname} style={{ animation: 'fadeInUp 0.3s ease-out forwards', height: '100%' }}>
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/intro" element={<SelfIntroductionMode />} />
                        <Route path="/debate" element={<DebateMode />} />
                        <Route path="/interview" element={<InterviewMode />} />
                        <Route path="*" element={<NotFound />} />
                    </Routes>
                </div>
            </main>
        </div>
    );
};

// GitHub Pages serves from /repo-name/ path, so React Router needs basename
const BASENAME = import.meta.env.BASE_URL || '/';

const App = () => {
    return (
        <AuthProvider>
            <Router basename={BASENAME}>
                <Routes>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/*" element={
                        <ProtectedRoute>
                            <AppLayout />
                        </ProtectedRoute>
                    } />
                </Routes>
            </Router>
        </AuthProvider>
    );
};

const styles = {
    layout: { display: 'flex', height: '100vh', width: '100vw' },
    sidebar: {
        width: '240px',
        background: '#0a0a0a',
        color: 'white',
        padding: '24px 0',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #1f2937',
    },
    brand: {
        fontSize: '1.3rem',
        fontWeight: '700',
        marginBottom: '24px',
        color: '#38bdf8',
        padding: '0 24px',
        letterSpacing: '-0.3px',
    },
    userCard: {
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '12px',
        background: 'rgba(56, 189, 248, 0.05)',
        borderRadius: '10px',
        margin: '0 14px 24px 14px',
        border: '1px solid rgba(56, 189, 248, 0.1)',
    },
    userAvatar: {
        width: '36px', height: '36px', borderRadius: '8px',
        background: 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.95rem', fontWeight: '700', color: '#fff', flexShrink: 0,
    },
    userInfo: { overflow: 'hidden' },
    userName: {
        fontSize: '0.85rem', fontWeight: '600', color: '#e2e8f0',
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
    },
    userEmail: {
        fontSize: '0.7rem', color: '#64748b',
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
    },
    links: { display: 'flex', flexDirection: 'column', gap: '4px' },
    link: {
        color: '#94a3b8',
        textDecoration: 'none',
        padding: '12px 24px',
        transition: 'all 0.2s ease',
        fontSize: '0.9rem',
        display: 'flex',
        alignItems: 'center',
    },
    sidebarBottom: { marginTop: 'auto', padding: '16px 14px 0 14px' },
    logoutBtn: {
        width: '100%', padding: '12px', borderRadius: '8px',
        border: '1px solid rgba(239, 68, 68, 0.2)', background: 'transparent',
        color: '#f87171', fontSize: '0.85rem', fontWeight: '600',
        cursor: 'pointer', transition: 'all 0.2s ease', fontFamily: "'Inter', sans-serif",
    },
    main: { flex: 1, overflowY: 'auto', background: '#000000', padding: '30px' },
};

export default App;