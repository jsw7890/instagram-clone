import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

const client = axios.create({
  baseURL,
  timeout: 60000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("ig_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

const AUTH_SKIP_REDIRECT = ["/auth/login", "/auth/signup", "/auth/me", "/admin"];

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const url = err.config?.url || "";
    const isAuthRoute = AUTH_SKIP_REDIRECT.some((p) => url.includes(p));
    if (err.response?.status === 401 && !isAuthRoute) {
      const hadToken = !!localStorage.getItem("ig_token");
      localStorage.removeItem("ig_token");
      if (hadToken && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export default client;
export { baseURL };
