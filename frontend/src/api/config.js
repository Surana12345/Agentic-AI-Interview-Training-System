// frontend/src/api/config.js
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const ENDPOINTS = {
    // Auth
    AUTH_LOGIN: `${API_BASE_URL}/api/auth/login`,
    AUTH_REGISTER: `${API_BASE_URL}/api/auth/register`,
    AUTH_ME: `${API_BASE_URL}/api/auth/me`,

    // Self-Introduction
    INTRO_UPLOAD: `${API_BASE_URL}/api/intro/upload-audio`,

    // Debate
    DEBATE_START: `${API_BASE_URL}/api/debate/start`,
    DEBATE_REPLY: `${API_BASE_URL}/api/debate/reply`,
    DEBATE_REPORT: `${API_BASE_URL}/api/debate/report`,

    // Interview
    INTERVIEW_START: `${API_BASE_URL}/api/interview/start`,
    INTERVIEW_REPLY: `${API_BASE_URL}/api/interview/reply`,
    INTERVIEW_REPORT: `${API_BASE_URL}/api/interview/report`,

    // Dashboard (supports ?user_id= query param)
    DASHBOARD_STATS: `${API_BASE_URL}/api/dashboard/stats`,

    // Orchestrator
    ORCHESTRATOR_REQUEST: `${API_BASE_URL}/api/orchestrator/request`,

    // Realtime (TTS + WebSocket)
    TTS_SYNTHESIZE: `${API_BASE_URL}/api/realtime/synthesize`,
    WS_COACHING: `${API_BASE_URL.replace('http', 'ws')}/api/realtime/ws/coaching`
};