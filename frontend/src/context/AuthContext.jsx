import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../utils/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('prism_token') || null);
  const [loading, setLoading] = useState(true);
  const [memory, setMemory] = useState(null);

  useEffect(() => {
    if (token) {
      localStorage.setItem('prism_token', token);
      fetchProfile();
    } else {
      localStorage.removeItem('prism_token');
      setUser(null);
      setMemory(null);
      setLoading(false);
    }
  }, [token]);

  const fetchProfile = async () => {
    try {
      const data = await authApi.getProfile();
      setUser({
        user_id: data.user_id,
        name: data.name,
        email: data.email
      });
      setMemory(data.memory);
    } catch (err) {
      console.error("Failed to fetch profile. Token might be expired.");
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    setLoading(true);
    try {
      const data = await authApi.login(email, password);
      setToken(data.token);
      return { success: true, ...data };
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    try {
      const data = await authApi.register(name, email, password);
      setToken(data.token);
      return { success: true, ...data };
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setMemory(null);
  };

  const updateMemory = (newMemory) => {
    setMemory(newMemory);
  };

  return (
    <AuthContext.Provider value={{
      user, token, loading, memory,
      login, register, logout, updateMemory,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
