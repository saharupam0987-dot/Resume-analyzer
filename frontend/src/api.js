import axios from 'axios';

/**
 * Production Axios API Client for the Evaluate Platform.
 * 
 * Interacts directly with the FastAPI backend at http://localhost:8000
 * (or configured VITE_API_URL).
 * Automatically injects JWT Bearer token into Authorization headers.
 * Catches 401 Unauthorized errors to handle expired tokens.
 */
const rawApiUrl = import.meta.env.VITE_API_URL;
const API_BASE_URL = (rawApiUrl !== undefined && rawApiUrl !== null && rawApiUrl !== '')
  ? rawApiUrl
  : (typeof window !== 'undefined' && window.location.port === '5173' ? 'http://localhost:8000' : '');

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 45000,
});

// Request interceptor: Attach JWT token if stored
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('eval_token');
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle expired tokens
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Don't clear on login attempt failures
      if (!error.config.url?.includes('/auth/login')) {
        console.warn('[Evaluate API] Session expired or unauthorized. Clearing stored token.');
        localStorage.removeItem('eval_token');
        localStorage.removeItem('eval_role');
        localStorage.removeItem('eval_user_id');
        localStorage.removeItem('eval_user_name');
        window.dispatchEvent(new Event('eval_auth_change'));
      }
    }
    return Promise.reject(error);
  }
);

const API = {
  baseURL: API_BASE_URL,
  get: (url, config) => http.get(url, config),
  post: (url, data, config) => http.post(url, data, config),
  put: (url, data, config) => http.put(url, data, config),
  delete: (url, config) => http.delete(url, config),
};

export default API;