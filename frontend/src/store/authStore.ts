import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, AuthState } from "@/types";

interface AuthStore extends AuthState {
  orgId: string | null;
  setAuth: (user: User, token: string, orgId: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      orgId: null,
      isAuthenticated: false,
      setAuth: (user, token, orgId) => {
        localStorage.setItem("access_token", token);
        set({ user, token, orgId, isAuthenticated: true });
      },
      clearAuth: () => {
        localStorage.removeItem("access_token");
        set({ user: null, token: null, orgId: null, isAuthenticated: false });
      },
    }),
    { name: "auth-storage", partialize: (s) => ({ user: s.user, token: s.token, orgId: s.orgId, isAuthenticated: s.isAuthenticated }) }
  )
);
