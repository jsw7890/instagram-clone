import { createContext, useContext, useEffect, useMemo, useState } from "react";
import * as authApi from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const persist = async (data) => {
    localStorage.setItem("ig_token", data.access_token);
    const full = await authApi.me();
    setUser(full);
  };

  useEffect(() => {
    const token = localStorage.getItem("ig_token");
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("ig_token");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      login: async (username, password) => {
        await persist(await authApi.login(username, password));
      },
      signup: async (payload) => {
        await persist(await authApi.signup(payload));
      },
      logout: () => {
        localStorage.removeItem("ig_token");
        setUser(null);
      },
      refreshMe: async () => setUser(await authApi.me()),
      setUser,
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
