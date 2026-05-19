import axios, { AxiosInstance, AxiosError } from "axios";
import { useAuthStore } from "@/store/authStore";

const configuredApiUrl = ((import.meta as any).env?.VITE_API_URL as string) || "/api";
const API_BASE_URL = configuredApiUrl.endsWith("/api")
  ? configuredApiUrl
  : `${configuredApiUrl.replace(/\/$/, "")}/api`;

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    const isLoginRequest = originalRequest?.url?.includes("login");

    if (
      error.response?.status === 401 &&
      !isLoginRequest &&
      !originalRequest._retry
    ) {
      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers["Authorization"] = "Bearer " + token;
            return axiosInstance(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = useAuthStore.getState().refreshToken;
        if (!refreshToken) throw new Error("Không có refresh token");

        const res = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          {},
          {
            headers: { Authorization: `Bearer ${refreshToken}` },
          },
        );

        const newToken = res.data.access_token;
        useAuthStore.getState().setTokens(newToken);

        processQueue(null, newToken);

        originalRequest.headers["Authorization"] = "Bearer " + newToken;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().logout();
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

export default axiosInstance;
