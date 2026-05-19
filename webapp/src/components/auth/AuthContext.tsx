import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { getMe } from '../../lib/api';

interface User {
  id: number;
  email: string;
  created_at: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  setAuth: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState>({
  token: null,
  user: null,
  loading: true,
  setAuth: () => {},
  logout: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem('bga_token');
    if (saved) {
      getMe(saved)
        .then((u) => {
          setToken(saved);
          setUser(u);
        })
        .catch(() => localStorage.removeItem('bga_token'))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  function setAuth(t: string, u: User) {
    localStorage.setItem('bga_token', t);
    setToken(t);
    setUser(u);
  }

  function logout() {
    localStorage.removeItem('bga_token');
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ token, user, loading, setAuth, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
