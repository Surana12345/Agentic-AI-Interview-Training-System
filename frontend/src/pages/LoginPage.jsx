import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const EyeIcon = ({ open }) => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {open ? (
            <>
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
            </>
        ) : (
            <>
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
                <line x1="1" y1="1" x2="23" y2="23" />
            </>
        )}
    </svg>
);

const PasswordInput = ({ value, onChange, placeholder = "••••••••", required = true }) => {
    const [show, setShow] = useState(false);
    return (
        <div style={styles.passwordWrapper}>
            <input
                type={show ? "text" : "password"}
                style={{ ...styles.input, paddingRight: '48px' }}
                placeholder={placeholder}
                value={value}
                onChange={onChange}
                required={required}
            />
            <button
                type="button"
                onClick={() => setShow(!show)}
                style={styles.eyeBtn}
                tabIndex={-1}
                aria-label={show ? "Hide password" : "Show password"}
            >
                <EyeIcon open={show} />
            </button>
        </div>
    );
};

const LoginPage = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [name, setName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login, register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            // Frontend validation for email format on BOTH login and register
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                throw new Error("Please enter a valid email address (e.g., name@example.com).");
            }

            // Additional register-only checks
            if (!isLogin) {
                if (password !== confirmPassword) {
                    throw new Error("Passwords do not match.");
                }
            }

            if (isLogin) {
                await login(email, password);
            } else {
                await register(name, email, password);
            }
            navigate('/');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={styles.container}>
            {/* Ambient Background Glows */}
            <div style={{ ...styles.glow, top: '-10%', left: '-10%', background: 'radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, transparent 70%)' }} />
            <div style={{ ...styles.glow, bottom: '-10%', right: '-10%', background: 'radial-gradient(circle, rgba(56, 189, 248, 0.1) 0%, transparent 70%)' }} />

            <div style={styles.card}>
                <div style={styles.header}>
                    <h1 style={styles.title}>AI Interview Training System</h1>
                    <p style={styles.subtitle}>{isLogin ? 'Sign in to practice' : 'Create an account'}</p>
                </div>

                <form onSubmit={handleSubmit} style={styles.form}>
                    {error && <div style={styles.error}>{error}</div>}

                    {!isLogin && (
                        <div style={styles.inputGroup}>
                            <label style={styles.label}>Full Name</label>
                            <input
                                type="text"
                                style={styles.input}
                                placeholder="Enter your name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                            />
                        </div>
                    )}

                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Email Address</label>
                        <input
                            type="email"
                            style={styles.input}
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div style={styles.inputGroup}>
                        <label style={styles.label}>Password</label>
                        <PasswordInput
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                        {!isLogin && (
                            <span style={styles.helperText}>
                                Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.
                            </span>
                        )}
                    </div>

                    {!isLogin && (
                        <div style={styles.inputGroup}>
                            <label style={styles.label}>Confirm Password</label>
                            <PasswordInput
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                        </div>
                    )}

                    <button type="submit" disabled={loading} style={{ ...styles.button, opacity: loading ? 0.7 : 1 }}>
                        {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
                    </button>
                </form>

                <div style={styles.toggleText}>
                    {isLogin ? "Don't have an account? " : "Already have an account? "}
                    <span style={styles.toggleLink} onClick={() => {
                        setIsLogin(!isLogin);
                        setError('');
                        setConfirmPassword('');
                    }}>
                        {isLogin ? 'Sign up' : 'Sign in'}
                    </span>
                </div>
            </div>
        </div>
    );
};

const styles = {
    container: {
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#000000',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: "'Inter', sans-serif"
    },
    glow: {
        position: 'absolute',
        width: '50vw',
        height: '50vw',
        borderRadius: '50%',
        pointerEvents: 'none',
        zIndex: 0
    },
    card: {
        position: 'relative',
        zIndex: 1,
        width: '100%',
        maxWidth: '420px',
        padding: '40px',
        backgroundColor: '#0a0a0a',
        border: '1px solid #1f2937',
        borderRadius: '24px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
    },
    header: {
        textAlign: 'center',
        marginBottom: '32px'
    },
    title: {
        fontSize: '1.5rem',
        fontWeight: '700',
        color: '#f8fafc',
        margin: '0 0 8px 0',
        letterSpacing: '-0.5px'
    },
    subtitle: {
        fontSize: '0.95rem',
        color: '#94a3b8',
        margin: 0
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
    },
    inputGroup: {
        display: 'flex',
        flexDirection: 'column',
        gap: '6px'
    },
    label: {
        fontSize: '0.85rem',
        fontWeight: '500',
        color: '#cbd5e1'
    },
    helperText: {
        fontSize: '0.75rem',
        color: '#64748b',
        marginTop: '2px',
        lineHeight: '1.4'
    },
    input: {
        width: '100%',
        padding: '12px 16px',
        backgroundColor: '#050505',
        border: '1px solid #1f2937',
        borderRadius: '12px',
        color: '#f8fafc',
        fontSize: '0.95rem',
        outline: 'none',
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        boxSizing: 'border-box',
    },
    passwordWrapper: {
        position: 'relative',
        width: '100%',
    },
    eyeBtn: {
        position: 'absolute',
        right: '12px',
        top: '50%',
        transform: 'translateY(-50%)',
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '6px',
        transition: 'background 0.15s ease',
    },
    button: {
        width: '100%',
        padding: '14px',
        marginTop: '8px',
        backgroundColor: '#38bdf8',
        color: '#000000',
        border: 'none',
        borderRadius: '12px',
        fontSize: '1rem',
        fontWeight: '700',
        cursor: 'pointer',
        transition: 'background-color 0.2s ease, transform 0.1s ease',
        boxShadow: '0 4px 12px rgba(56, 189, 248, 0.3)'
    },
    error: {
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.2)',
        color: '#ef4444',
        padding: '12px',
        borderRadius: '8px',
        fontSize: '0.85rem',
        textAlign: 'center'
    },
    toggleText: {
        marginTop: '24px',
        textAlign: 'center',
        fontSize: '0.9rem',
        color: '#94a3b8'
    },
    toggleLink: {
        color: '#38bdf8',
        fontWeight: '600',
        cursor: 'pointer',
        textDecoration: 'none'
    }
};

export default LoginPage;
