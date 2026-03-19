import axios, { AxiosError } from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const detail =
      (error.response?.data as { detail?: string })?.detail ??
      error.message ??
      "An unexpected error occurred";
    return Promise.reject(new Error(String(detail)));
  }
);

export default api;
