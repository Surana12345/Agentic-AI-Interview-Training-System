/**
 * Authenticated fetch helper.
 * Automatically attaches the JWT token from localStorage to all requests.
 */

/**
 * Get the auth headers with Bearer token.
 * @returns {Object} Headers object with Authorization if token exists
 */
export function getAuthHeaders() {
    const token = localStorage.getItem('auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Wrapper around fetch that automatically includes the JWT Authorization header.
 * For FormData requests, do NOT set Content-Type (browser sets multipart boundary).
 * 
 * @param {string} url - The URL to fetch
 * @param {Object} options - Standard fetch options
 * @returns {Promise<Response>}
 */
export async function authFetch(url, options = {}) {
    const token = localStorage.getItem('auth_token');
    const headers = { ...options.headers };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(url, { ...options, headers });
}
