import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { fetchMe, login as apiLogin, readToken, writeToken } from "./api";
import type { Me, Role } from "./types";

interface AuthState {
  me: Me | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  can: (permission: string) => boolean;
  isRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = readToken();
    if (!token) {
      setLoading(false);
      return;
    }
    fetchMe()
      .then((value) => {
        setMe(value);
      })
      .catch(() => {
        writeToken(null);
        setMe(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      me,
      loading,
      error,
      login: async (username: string, password: string) => {
        setError(null);
        const token = await apiLogin(username, password);
        writeToken(token);
        const profile = await fetchMe();
        setMe(profile);
      },
      logout: () => {
        writeToken(null);
        setMe(null);
      },
      can: (permission: string) => Boolean(me?.permissions.includes(permission)),
      isRole: (...roles: Role[]) => Boolean(me && roles.includes(me.role)),
    }),
    [error, loading, me],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
