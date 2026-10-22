import axios, { AxiosError, type AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/features/auth/store";
import { API_BASE } from "@/constants/config";

const api: AxiosInstance = axios.create({
   baseURL: API_BASE,
   headers: { "Content-Type": "application/json" },
   withCredentials: true,
});

const isRefreshFailed = () => sessionStorage.getItem("refreshFailed") === "true";
const setRefreshFailed = () => sessionStorage.setItem("refreshFailed", "true");
export const clearRefreshFailed = () => sessionStorage.removeItem("refreshFailed");

// Auth endpoints answer 401 for bad credentials/tokens; refreshing there makes no sense.
const NO_REFRESH_URLS = ["/auth/login", "/auth/register", "/auth/token", "/auth/refresh"];

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
         NO_REFRESH_URLS.some((url) => originalRequest.url?.includes(url)) ||
         isRefreshFailed()
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
         const { data } = await axios.post<{ accessToken: string }>(
            `${API_BASE}/auth/refresh`,
            {}, // empty body, cookie is sent automatically
            { withCredentials: true, _skipRefresh: true } as any,
         );
         clearRefreshFailed();
         useAuthStore.getState().setAccessToken(data.accessToken);
         processQueue(null);
         return api(originalRequest);
      } catch (refreshError) {
         setRefreshFailed(); // persists across the page reload
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
