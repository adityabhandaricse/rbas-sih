import axios from "axios";

// Default to http://127.0.0.1:8000/api if no environment variable is defined
const rawBaseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
const cleanBaseURL = rawBaseURL.replace(/\/+$/, ""); // Remove trailing slash

const api = axios.create({
  baseURL: cleanBaseURL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60s timeout ceiling to accommodate AI inference cycles
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("gramsetu_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status;
    const url = error?.config?.url;
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      "Something went wrong talking to the server.";

    console.error(`[API Error] Status: ${status} | Route: ${url} | Message:`, message);
    
    // Attach response data directly to error for cleaner downstream inspection
    const enhancedError = new Error(message);
    enhancedError.response = error.response;
    enhancedError.status = status;
    return Promise.reject(enhancedError);
  }
);

// Helper function that attempts primary route and falls back if backend uses flat naming
async function postWithFallback(primaryPath, fallbackPath, payload) {
  try {
    const res = await api.post(primaryPath, payload);
    return res.data;
  } catch (err) {
    const is404 = err.status === 404 || err.response?.status === 404 || err.message?.includes("404");
    if (fallbackPath && is404) {
      console.warn(`[API Fallback] ${primaryPath} returned 404. Attempting fallback: ${fallbackPath}...`);
      const res = await api.post(fallbackPath, payload);
      return res.data;
    }
    throw err;
  }
}

// Deterministic Loan Structuring
export const structureLoan = (marginCapital) =>
  postWithFallback("/finance/structure-loan/", "/structure-loan/", { margin_capital: marginCapital });

// Live Competitor Density & Saturation Mapping (Overpass OSM)
export const competitorsDensity = (payload) =>
  postWithFallback("/competitors/density/", "/competitors-density/", payload);

// AI Feasibility Study (Mistral Structured Output)
export const generateFeasibility = (payload) =>
  postWithFallback("/feasibility/generate/", "/feasibility/", payload);

// Single-Roundtrip Full Feasibility Evaluation
export const fullFeasibilityEvaluation = (payload) =>
  postWithFallback("/feasibility/evaluate/", "/feasibility-evaluate/", payload);

// Citizen Authentication / User Token Generation
export const otpLogin = (payload) =>
  postWithFallback("/auth/otp-login/", "/otp-login/", payload);

export default api;