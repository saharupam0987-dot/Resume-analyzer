import React, { useState, useEffect } from 'react';
import { ToastProvider, useToast } from './components/ui';
import { AppShell } from './components/AppShell';
import AuthScreen from './components/AuthScreen';

// Load stored session credentials only if real token exists
function getSession() {
  try {
    const token = localStorage.getItem('eval_token');
    const role = localStorage.getItem('eval_role');
    if (!token || token === 'demo_token') {
      localStorage.removeItem('eval_token');
      localStorage.removeItem('eval_role');
      return { token: null, role: null };
    }
    return { token, role: role || 'teacher' };
  } catch {
    return { token: null, role: null };
  }
}

export default function App() {
  const [session, setSession] = useState(getSession);

  useEffect(() => {
    const handleAuthChange = () => {
      setSession(getSession());
    };
    window.addEventListener('eval_auth_change', handleAuthChange);
    return () => window.removeEventListener('eval_auth_change', handleAuthChange);
  }, []);

  const setToken = (tok) => {
    if (tok) {
      localStorage.setItem('eval_token', tok);
    } else {
      localStorage.removeItem('eval_token');
    }
    setSession(getSession());
  };

  const setRole = (r) => {
    if (r) {
      localStorage.setItem('eval_role', r);
    } else {
      localStorage.removeItem('eval_role');
    }
    setSession(getSession());
  };

  return (
    <ToastProvider>
      {!session.token ? (
        <AuthScreen setToken={setToken} setRole={setRole} />
      ) : (
        <AppShell 
          token={session.token} 
          setToken={setToken} 
          role={session.role} 
          setRole={setRole} 
        />
      )}
    </ToastProvider>
  );
}

export { useToast };