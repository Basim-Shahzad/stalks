import axios, { AxiosError, create, type AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/features/auth/store";
import { API_BASE } from "@/constants/config";

const api: AxiosInstance = create({
   baseURL: API_BASE,
   headers: { "Content-Type": "application/json" },
   withCredentials: true,
});

let isRefreshing = false;
let failedQueue: {
   resolve: (value?: unknown) => void;
   reject: (reason?: unknown) => void;
}[] = [];

const processQueue = (error: unknown) => {
   failedQueue.forEach(({ resolve, reject }) => (error ? reject(error) : resolve()));
   failedQueue = [];
};

api.interceptors.request.use((config) => {
   const accessToken = useAuthStore.getState().accessToken;
   if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
   }
   return config;
});

api.interceptors.response.use(
   (response) => response,
   async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & {
         _retry?: boolean;
         _skipRefresh?: boolean;
      };

      if (
         error.response?.status !== 401 ||
         originalRequest._retry ||
         originalRequest._skipRefresh ||
         originalRequest.url?.includes("/auth/refresh")
      ) {
         return Promise.reject(error);
      }

      if (isRefreshing) {
         return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
         })
            .then(() => api(originalRequest))
            .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
         const { data } = await axios.post<{ accessToken: string }>(`${API_BASE}/auth/refresh`, {}, {
            withCredentials: true,
            _skipRefresh: true,
         } as any);

         useAuthStore.getState().setAccessToken(data.accessToken);
         processQueue(null);
         return api(originalRequest);
      } catch (refreshError) {
         processQueue(refreshError);
         useAuthStore.getState().logout();
         window.location.href = "/login";
         return Promise.reject(refreshError);
      } finally {
         isRefreshing = false;
      }
   },
);

export default api;
