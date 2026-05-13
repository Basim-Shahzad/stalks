import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User } from "@/types/auth.types";

interface AuthState {
   user: User | null;
   accessToken: string | null;
   isInitialized: boolean; // Used for the initial server-side/client-side sync check

   setAuthInitialized: (user: User | null) => void;
   setAccessToken: (token: string) => void;
   login: (user: User, accessToken: string) => void;
   logout: () => void;
}

export const useAuthStore = create<AuthState>()(
   persist(
      (set) => ({
         user: null,
         accessToken: null,
         isInitialized: false,

         setAuthInitialized: (user) => set({ user, isInitialized: true }),
         setAccessToken: (token) => set({ accessToken: token }),
         login: (user, accessToken) => set({ user, accessToken }),
         logout: () => {
            set({ user: null, accessToken: null });
            localStorage.removeItem("auth-storage"); // Force clear on logout
         },
      }),
      {
         name: "auth-storage",
         storage: createJSONStorage(() => localStorage),
         // Only persist user and token; don't persist initialization state
         partialize: (state) => ({
            user: state.user,
            accessToken: state.accessToken,
         }),
      },
   ),
);
