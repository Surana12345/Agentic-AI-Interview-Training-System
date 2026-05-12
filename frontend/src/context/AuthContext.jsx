import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_BASE_URL } from '../api/config';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

/**
 * Safely parse JSON from a fetch Response.
 * Returns null if parsing fails (e.g. empty body, HTML error page).
 */
async function safeJson(res) {
    try {
        const text = await res.text();
        if (!text || text.trim().length === 0) return null;
        return JSON.parse(text);
    } catch {
        return null;
    }
}

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(localStorage.getItem('auth_token'));
    const [loading, setLoading] = useState(true);

    // On mount, validate the stored token
    useEffect(() => {
        const validateToken = async () => {
            const storedToken = localStorage.getItem('auth_token');
            if (!storedToken) {
                setLoading(false);
                return;
            }
            try {
                const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
                    headers: { Authorization: `Bearer ${storedToken}` },
                });
                if (res.ok) {
                    const userData = await safeJson(res);
                    if (userData) {
                        setUser(userData);
                        setToken(storedToken);
                    }
                } else {
                    // Token is invalid/expired — clear it
                    localStorage.removeItem('auth_token');
                    localStorage.removeItem('auth_user');
                    setToken(null);
                    setUser(null);
                }
            } catch (err) {
                console.error('Token validation failed:', err);
                // If server is unreachable, use cached user data
                const cachedUser = localStorage.getItem('auth_user');
                if (cachedUser) {
                    try { setUser(JSON.parse(cachedUser)); } catch { /* ignore */ }
                }
            }
            setLoading(false);
        };
        validateToken();
    }, []);

    const login = async (email, password) => {
        let res;
        try {
            res = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
        } catch (err) {
            throw new Error('Cannot connect to server. Make sure the backend is running on port 8000.');
        }

        const data = await safeJson(res);
        if (!res.ok) {
            const message = (data && data.detail) ? data.detail : `Login failed (status ${res.status})`;
            throw new Error(message);
        }
        if (!data || !data.access_token) {
            throw new Error('Invalid response from server.');
        }

        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('auth_user', JSON.stringify(data.user));
        setToken(data.access_token);
        setUser(data.user);
        return data;
    };

    const register = async (name, email, password) => {
        let res;
        try {
            res = await fetch(`${API_BASE_URL}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password }),
            });
        } catch (err) {
            throw new Error('Cannot connect to server. Make sure the backend is running on port 8000.');
        }

        const data = await safeJson(res);
        if (!res.ok) {
            const message = (data && data.detail) ? data.detail : `Registration failed (status ${res.status})`;
            throw new Error(message);
        }
        if (!data || !data.access_token) {
            throw new Error('Invalid response from server.');
        }

        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('auth_user', JSON.stringify(data.user));
        setToken(data.access_token);
        setUser(data.user);
        return data;
    };

    const logout = () => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
