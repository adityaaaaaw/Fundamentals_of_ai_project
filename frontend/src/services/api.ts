import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 seconds for standard database operations
});

export const aiApiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds dedicated timeout for multi-step AI Agent requests
});

const formatErrorMessage = (error: any): string => {
  // Check for client-side timeout
  if (error.code === 'ECONNABORTED' || (error.message && error.message.toLowerCase().includes('timeout'))) {
    return 'The AI Agent request timed out. Gemini took longer than expected to process your request. Please try again.';
  }

  // Network connection error
  if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
    return 'Unable to reach the backend server. Please verify that the FastAPI backend is running on port 8000.';
  }

  // Backend detail message
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    const detailStr = typeof detail === 'string' ? detail : JSON.stringify(detail);

    if (error.response.status === 429 || detailStr.includes('rate limit')) {
      return 'Gemini API rate limit reached. Please wait a moment before sending another prompt.';
    }
    if (error.response.status === 503 || detailStr.includes('high demand') || detailStr.includes('temporarily')) {
      return 'The AI model is temporarily experiencing high demand. Please try again in a few moments.';
    }
    if (error.response.status === 504 || detailStr.includes('timed out')) {
      return 'The AI request timed out on the server. Please try again with a more specific question.';
    }
    if (error.response.status === 401 || detailStr.includes('authentication') || detailStr.includes('API key')) {
      return 'AI authentication failed. Please verify that GEMINI_API_KEY is configured in backend/.env.';
    }
    return detailStr;
  }

  if (error.message) {
    return error.message;
  }

  return 'An unexpected network error occurred. Please try again.';
};

// Response error handler to extract student-friendly error details
const attachInterceptor = (instance: typeof apiClient) => {
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      const message = formatErrorMessage(error);
      return Promise.reject(new Error(message));
    }
  );
};

attachInterceptor(apiClient);
attachInterceptor(aiApiClient);

export default apiClient;

