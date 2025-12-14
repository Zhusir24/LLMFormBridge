import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useSnapshot } from 'valtio';
import { Box, CircularProgress } from '@mui/material';

import { authStore } from './store/auth';
import { authService } from './services/auth';
import Layout from './components/common/Layout';
import NotificationManager from './components/common/NotificationManager';
import LoginPage from './pages/Login';
import Dashboard from './pages/Dashboard';
import Credentials from './pages/Credentials';
import Models from './pages/Models';
import Logs from './pages/Logs';

// 私有路由组件
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useSnapshot(authStore);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

// 公共路由组件（已登录用户重定向到dashboard）
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useSnapshot(authStore);
  return isAuthenticated ? <Navigate to="/" /> : <>{children}</>;
};

function App() {
  const { token } = useSnapshot(authStore);

  useEffect(() => {
    // 初始化时检查是否有有效的token
    const initAuth = async () => {
      if (token) {
        authStore.isLoading = true;
        try {
          const user = await authService.getCurrentUser();
          authStore.user = user;
          authStore.isAuthenticated = true;
        } catch (error) {
          // Token无效，清除状态
          authStore.token = null;
          authStore.refreshToken = null;
          authStore.user = null;
          authStore.isAuthenticated = false;
        } finally {
          authStore.isLoading = false;
        }
      }
    };

    initAuth();
  }, [token]);

  return (
    <>
      <NotificationManager />
      <Routes>
        {/* 公共路由 */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />

        {/* 私有路由 */}
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="credentials" element={<Credentials />} />
          <Route path="models" element={<Models />} />
          <Route path="logs" element={<Logs />} />
        </Route>

        {/* 404路由 */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  );
}

export default App;