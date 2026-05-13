import { useAuthStore } from "@/stores/useAuthStore";
import api from "@/services/api.service";
import type { User, Tokens } from "@/types/auth.types";

export const useAuth = {
   signup: async (signupData: { name: string; email: string; password: string; isActive: true }) => {
      const { data: signupResData } = await api.post<User>("/auth/register", signupData);

      const { data: loginResData } = await api.post<Tokens>("/auth/login", {
         email: signupData.email,
         password: signupData.password,
      });

      useAuthStore.getState().login(signupResData, loginResData.accessToken);
      return signupResData;
   },

   login: async (loginData: { email: string; password: string }) => {
      const { data: loginResData } = await api.post<Tokens>("/auth/login", loginData);

      const { data: meData } = await api.get<User>("/auth/me", {
         headers: {
            Authorization: `Bearer ${loginResData.accessToken}`,
         },
      });

      useAuthStore.getState().login(meData, loginResData.accessToken);
      return meData;
   },

   logout: async () => {
      const logoutRes = await api.post("/auth/logout", {}, { withCredentials: true });
      if (logoutRes.status === 204) {
         useAuthStore.getState().logout();
      }
   },

   me: async () => {
      const { data: meData } = await api.get<User>("/auth/me");
      // single atomic update — user and isInitialized set together, one render
      useAuthStore.getState().setAuthInitialized(meData);
      return meData;
   },
};
