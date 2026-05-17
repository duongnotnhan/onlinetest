import { create } from "zustand";

interface User {
  user_id: number;
  username: string;
  email: string;
  full_name: string;
  role: "admin" | "teacher" | "student";
  is_active: boolean;
  is_first_login?: boolean;
  two_fa_enabled?: boolean;
  teacher_type?: string;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string, refreshToken: string) => void;
  logout: () => void;
  setUser: (user: User) => void;
  setTokens: (token: string, refreshToken?: string) => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: JSON.parse(localStorage.getItem("user") || "null"),
  token: localStorage.getItem("token"),
  refreshToken: localStorage.getItem("refresh_token"),
  isAuthenticated: !!localStorage.getItem("token"),

  login: (user, token, refreshToken) => {
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("token", token);
    localStorage.setItem("refresh_token", refreshToken);
    set({ user, token, refreshToken, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    set({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  },

  setUser: (user) => {
    localStorage.setItem("user", JSON.stringify(user));
    set({ user });
  },

  setTokens: (token, refreshToken) => {
    localStorage.setItem("token", token);
    if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
    set((state) => ({
      ...state,
      token,
      refreshToken: refreshToken || state.refreshToken,
    }));
  },
}));
