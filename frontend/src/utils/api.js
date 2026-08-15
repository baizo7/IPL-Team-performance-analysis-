import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const API_BASE = `${BASE_URL.replace(/\/$/, '')}/api`;

const api = axios.create({
  baseURL: API_BASE,
});

// Automatically inject JWT Bearer Token if present in localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ipl_jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
