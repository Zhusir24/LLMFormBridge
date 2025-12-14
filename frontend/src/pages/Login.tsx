import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Box,
  TextField,
  Button,
  Typography,
  Tab,
  Tabs,
  Alert,
  CircularProgress,
} from '@mui/material';
import { authStore } from '../store/auth';
import { authService } from '../services/auth';
import { addNotification } from '../store/ui';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`auth-tabpanel-${index}`}
      aria-labelledby={`auth-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 登录表单
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: '',
  });

  // 注册表单
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  // 表单验证错误
  const [validationErrors, setValidationErrors] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
    setError('');
    setValidationErrors({
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    });
  };

  // 验证注册表单
  const validateRegisterForm = (): boolean => {
    const errors = {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    };

    let isValid = true;

    // 验证用户名
    if (!registerForm.username) {
      errors.username = '用户名不能为空';
      isValid = false;
    } else if (registerForm.username.length < 3) {
      errors.username = '用户名至少需要3个字符';
      isValid = false;
    } else if (registerForm.username.length > 50) {
      errors.username = '用户名不能超过50个字符';
      isValid = false;
    }

    // 验证邮箱
    if (!registerForm.email) {
      errors.email = '邮箱不能为空';
      isValid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerForm.email)) {
      errors.email = '请输入有效的邮箱地址';
      isValid = false;
    }

    // 验证密码
    if (!registerForm.password) {
      errors.password = '密码不能为空';
      isValid = false;
    } else if (registerForm.password.length < 6) {
      errors.password = '密码至少需要6个字符';
      isValid = false;
    } else if (registerForm.password.length > 100) {
      errors.password = '密码不能超过100个字符';
      isValid = false;
    }

    // 验证确认密码
    if (!registerForm.confirmPassword) {
      errors.confirmPassword = '请确认密码';
      isValid = false;
    } else if (registerForm.password !== registerForm.confirmPassword) {
      errors.confirmPassword = '两次输入的密码不一致';
      isValid = false;
    }

    setValidationErrors(errors);
    return isValid;
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const tokens = await authService.login(loginForm);

      // 先设置token，再获取用户信息
      authStore.token = tokens.access_token;
      authStore.refreshToken = tokens.refresh_token;

      const user = await authService.getCurrentUser();
      authStore.user = user;
      authStore.isAuthenticated = true;

      addNotification({
        type: 'success',
        title: '登录成功',
        message: `欢迎回来，${user.username}！`,
      });

      navigate('/');
    } catch (error: any) {
      console.error('登录错误：', error);
      console.error('错误响应：', error.response);
      console.error('错误数据：', error.response?.data);
      const errorMessage = error.response?.data?.detail || '登录失败，请检查用户名和密码';
      console.log('设置错误消息：', errorMessage);
      setError(errorMessage);
      console.log('错误已设置');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // 先进行客户端验证
    if (!validateRegisterForm()) {
      return;
    }

    setLoading(true);

    try {
      await authService.register({
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password,
      });

      addNotification({
        type: 'success',
        title: '注册成功',
        message: '账户创建成功，请登录',
      });

      // 清空注册表单
      setRegisterForm({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
      });
      
      setTab(0); // 切换到登录标签
    } catch (error: any) {
      console.error('注册错误：', error);
      
      // 处理422验证错误
      let errorMessage = '注册失败，请重试';
      
      if (error.response?.status === 422 && error.response?.data?.detail) {
        const details = error.response.data.detail;
        
        // FastAPI的422错误返回一个数组格式的详细错误信息
        if (Array.isArray(details)) {
          const errorMessages = details.map((err: any) => {
            const field = err.loc?.[err.loc.length - 1] || '字段';
            const fieldName = {
              username: '用户名',
              email: '邮箱',
              password: '密码'
            }[field] || field;
            
            return `${fieldName}: ${err.msg}`;
          }).join('；');
          
          errorMessage = errorMessages || errorMessage;
        } else if (typeof details === 'string') {
          errorMessage = details;
        }
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ width: '100%', overflow: 'hidden' }}>
          <Box sx={{ textAlign: 'center', pt: 3, pb: 1 }}>
            <Typography component="h1" variant="h4" gutterBottom>
              LLMFormBridge
            </Typography>
            <Typography variant="body2" color="text.secondary">
              LLM服务转接平台
            </Typography>
          </Box>

          <Tabs value={tab} onChange={handleTabChange} centered>
            <Tab label="登录" />
            <Tab label="注册" />
          </Tabs>

          {error && (
            <Box sx={{ px: 2, pt: 2 }}>
              <Alert 
                severity="error" 
                onClose={() => setError('')}
                sx={{ mb: 0 }}
              >
                {error}
              </Alert>
            </Box>
          )}
          
          {/* 调试信息 */}
          {console.log('当前错误状态：', error)}

          <TabPanel value={tab} index={0}>
            <Box component="form" onSubmit={handleLogin} noValidate>
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="用户名"
                name="username"
                autoComplete="username"
                autoFocus
                value={loginForm.username}
                onChange={(e) => {
                  setLoginForm({ ...loginForm, username: e.target.value });
                  if (error) setError(''); // 清除错误
                }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="密码"
                type="password"
                id="password"
                autoComplete="current-password"
                value={loginForm.password}
                onChange={(e) => {
                  setLoginForm({ ...loginForm, password: e.target.value });
                  if (error) setError(''); // 清除错误
                }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : '登录'}
              </Button>
            </Box>
          </TabPanel>

          <TabPanel value={tab} index={1}>
            <Box component="form" onSubmit={handleRegister} noValidate>
              <TextField
                margin="normal"
                required
                fullWidth
                id="register-username"
                label="用户名"
                name="username"
                autoComplete="username"
                value={registerForm.username}
                onChange={(e) => {
                  setRegisterForm({ ...registerForm, username: e.target.value });
                  setValidationErrors({ ...validationErrors, username: '' });
                }}
                error={!!validationErrors.username}
                helperText={validationErrors.username || '用户名长度需在3-50个字符之间'}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="邮箱地址"
                name="email"
                autoComplete="email"
                type="email"
                value={registerForm.email}
                onChange={(e) => {
                  setRegisterForm({ ...registerForm, email: e.target.value });
                  setValidationErrors({ ...validationErrors, email: '' });
                }}
                error={!!validationErrors.email}
                helperText={validationErrors.email || '请输入有效的邮箱地址'}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="密码"
                type="password"
                id="register-password"
                autoComplete="new-password"
                value={registerForm.password}
                onChange={(e) => {
                  setRegisterForm({ ...registerForm, password: e.target.value });
                  setValidationErrors({ ...validationErrors, password: '' });
                }}
                error={!!validationErrors.password}
                helperText={validationErrors.password || '密码长度需在6-100个字符之间'}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="confirmPassword"
                label="确认密码"
                type="password"
                id="confirm-password"
                value={registerForm.confirmPassword}
                onChange={(e) => {
                  setRegisterForm({ ...registerForm, confirmPassword: e.target.value });
                  setValidationErrors({ ...validationErrors, confirmPassword: '' });
                }}
                error={!!validationErrors.confirmPassword}
                helperText={validationErrors.confirmPassword || '请再次输入密码'}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : '注册'}
              </Button>
            </Box>
          </TabPanel>
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage;