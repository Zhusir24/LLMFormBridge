interface AppConfig {
  appName: string;
  appVersion: string;
  apiBaseUrl: string;
  backendUrl: string;
  isDevelopment: boolean;
  enableDebug: boolean;
  enableMockData: boolean;
  themeColor: string;
  defaultLanguage: string;
  frontendPort: number;
  backendPort: number;
  backendHost: string;
}

const config: AppConfig = {
  appName: import.meta.env.VITE_APP_NAME || 'LLMFormBridge',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  backendUrl: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
  isDevelopment: import.meta.env.VITE_NODE_ENV === 'development',
  enableDebug: import.meta.env.VITE_ENABLE_DEBUG === 'true',
  enableMockData: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true',
  themeColor: import.meta.env.VITE_THEME_COLOR || '#3b82f6',
  defaultLanguage: import.meta.env.VITE_DEFAULT_LANGUAGE || 'zh-CN',
  frontendPort: parseInt(import.meta.env.VITE_FRONTEND_PORT) || 3000,
  backendPort: parseInt(import.meta.env.VITE_BACKEND_PORT) || 8000,
  backendHost: import.meta.env.VITE_BACKEND_HOST || 'localhost',
};

export default config;

export const getApiUrl = (endpoint: string): string => {
  return `${config.apiBaseUrl}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
};

export const getBackendUrl = (path: string = ''): string => {
  return `${config.backendUrl}${path.startsWith('/') ? path : '/' + path}`;
};