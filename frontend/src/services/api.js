/**
 * api.js — Centralised API client for PRISM frontend.
 * Automatically attaches JWT token to all requests if available.
 */

const BASE_URL = (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000') + '/api';
let authToken = null;

export const api = {
  setToken: (token) => {
    authToken = token;
  },

  _request: async (endpoint, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const config = {
      ...options,
      headers,
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.message || 'API request failed');
    }

    return data;
  },

  // Auth
  login: (email, password) => 
    api._request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    }),

  register: (name, email, password) => 
    api._request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password })
    }),

  getProfile: () => 
    api._request('/auth/me', { method: 'GET' }),

  getMemory: () => 
    api._request('/auth/memory', { method: 'GET' }),

  chooseProduct: (productId) => 
    api._request('/auth/choose-product', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId })
    }),

  // Core PRISM
  analyze: (payload) => 
    api._request('/prism/analyze', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
    
  getHistory: () =>
    api._request('/sessions/history', { method: 'GET' })
};
