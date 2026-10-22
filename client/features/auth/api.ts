import { useAuthStore } from "./store";
import api, { clearRefreshFailed } from "@/services/api.service";
import type { User, Tokens } from "./types";
import { API_BASE } from "@/constants/config";
import axios from "axios";

export const useAuth = {
   signup: async (signupData: { name: string; email: string; password: string }) => {
      const { data: signupResData } = await api.post<User>("/auth/register", signupData);

      const { data: loginResData } = await api.post<Tokens>("/auth/login", {
         email: signupData.email,
         password: signupData.password,
      });

      clearRefreshFailed();
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

      clearRefreshFailed();
      useAuthStore.getState().login(meData, loginResData.accessToken);
      return meData;
   },

   logout: async () => {
      try {
         await api.post("/auth/logout", {}, { withCredentials: true });
      } finally {
         // Always drop local session state, even if the server call failed.
         useAuthStore.getState().logout();
      }
   },

   me: async () => {
      if (!useAuthStore.getState().accessToken) {
         try {
            const { data: refreshData } = await axios.post<{ accessToken: string }>(
               `${API_BASE}/auth/refresh`,
               {},
               { withCredentials: true }, // plain axios — no interceptor
            );
            clearRefreshFailed();
            useAuthStore.getState().setAccessToken(refreshData.accessToken);
         } catch {
            // No valid cookie — stop here, don't call /me
            useAuthStore.getState().setAuthInitialized(null);
            return null;
         }
      }

      const { data: meData } = await api.get<User>("/auth/me");
      useAuthStore.getState().setAuthInitialized(meData);
      return meData;
   },
};
