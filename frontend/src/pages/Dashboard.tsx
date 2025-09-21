import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  IconButton,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  VpnKey,
  Settings,
  Assessment,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSnapshot } from 'valtio';
import { credentialStore } from '../store/credentials';
import { modelStore } from '../store/models';
import { credentialService } from '../services/credentials';
import { modelService } from '../services/models';
import { addNotification } from '../store/ui';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { credentials } = useSnapshot(credentialStore);
  const { modelConfigs } = useSnapshot(modelStore);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [credentialsData, modelsData] = await Promise.all([
        credentialService.getCredentials(),
        modelService.getModelConfigs(),
      ]);

      credentialStore.credentials = credentialsData;
      modelStore.modelConfigs = modelsData;
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: '加载失败',
        message: error.response?.data?.detail || '无法加载仪表板数据',
      });
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    totalCredentials: credentials.length,
    validatedCredentials: credentials.filter(c => c.is_validated).length,
    totalModels: modelConfigs.length,
    enabledModels: modelConfigs.filter(m => m.is_enabled).length,
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          仪表板
        </Typography>
        <IconButton onClick={loadDashboardData} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      {/* 统计卡片 */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    总凭证数
                  </Typography>
                  <Typography variant="h4">
                    {stats.totalCredentials}
                  </Typography>
                </Box>
                <VpnKey color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    已验证凭证
                  </Typography>
                  <Typography variant="h4">
                    {stats.validatedCredentials}
                  </Typography>
                </Box>
                <CheckCircle color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    模型配置数
                  </Typography>
                  <Typography variant="h4">
                    {stats.totalModels}
                  </Typography>
                </Box>
                <Settings color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    启用的模型
                  </Typography>
                  <Typography variant="h4">
                    {stats.enabledModels}
                  </Typography>
                </Box>
                <Assessment color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 快速操作 */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                快速操作
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => navigate('/credentials')}
                >
                  添加凭证
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Settings />}
                  onClick={() => navigate('/models')}
                >
                  配置模型
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Assessment />}
                  onClick={() => navigate('/logs')}
                >
                  查看日志
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                系统状态
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Typography>API服务</Typography>
                  <Chip
                    icon={<CheckCircle />}
                    label="正常"
                    color="success"
                    size="small"
                  />
                </Box>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Typography>数据库连接</Typography>
                  <Chip
                    icon={<CheckCircle />}
                    label="正常"
                    color="success"
                    size="small"
                  />
                </Box>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Typography>LLM适配器</Typography>
                  <Chip
                    icon={<CheckCircle />}
                    label="正常"
                    color="success"
                    size="small"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 最近的凭证和模型 */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                最近的凭证
              </Typography>
              {credentials.length === 0 ? (
                <Typography color="textSecondary">
                  暂无凭证，请先添加LLM服务凭证
                </Typography>
              ) : (
                <Box display="flex" flexDirection="column" gap={1}>
                  {credentials.slice(0, 5).map((credential) => (
                    <Box
                      key={credential.id}
                      display="flex"
                      alignItems="center"
                      justifyContent="space-between"
                      p={1}
                      border={1}
                      borderColor="divider"
                      borderRadius={1}
                    >
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {credential.name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {credential.provider.toUpperCase()}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        {credential.is_validated ? (
                          <CheckCircle color="success" fontSize="small" />
                        ) : credential.validation_error ? (
                          <Error color="error" fontSize="small" />
                        ) : (
                          <Warning color="warning" fontSize="small" />
                        )}
                        <Chip
                          label={credential.is_active ? '活跃' : '禁用'}
                          color={credential.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                最近的模型配置
              </Typography>
              {modelConfigs.length === 0 ? (
                <Typography color="textSecondary">
                  暂无模型配置，请先配置模型转发规则
                </Typography>
              ) : (
                <Box display="flex" flexDirection="column" gap={1}>
                  {modelConfigs.slice(0, 5).map((model) => (
                    <Box
                      key={model.id}
                      display="flex"
                      alignItems="center"
                      justifyContent="space-between"
                      p={1}
                      border={1}
                      borderColor="divider"
                      borderRadius={1}
                    >
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {model.model_name}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {model.credential_provider.toUpperCase()} → {model.target_format.toUpperCase()}
                        </Typography>
                      </Box>
                      <Chip
                        label={model.is_enabled ? '启用' : '禁用'}
                        color={model.is_enabled ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;