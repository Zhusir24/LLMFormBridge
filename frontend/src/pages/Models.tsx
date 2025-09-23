import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  Key as KeyIcon,
} from '@mui/icons-material';
import { useSnapshot } from 'valtio';
import { modelStore } from '../store/models';
import { credentialStore } from '../store/credentials';
import { modelService } from '../services/models';
import { credentialService } from '../services/credentials';
import { addNotification } from '../store/ui';
import { ModelConfigCreate, TargetFormat } from '../types/model';

const Models: React.FC = () => {
  const { modelConfigs, isLoading } = useSnapshot(modelStore);
  const { credentials } = useSnapshot(credentialStore);
  const [open, setOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<any>(null);

  const [formData, setFormData] = useState<ModelConfigCreate>({
    credential_id: '',
    model_name: '',
    target_format: 'openai',
    is_enabled: true,
    rate_limit: 100,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    modelStore.isLoading = true;
    try {
      const [modelsData, credentialsData] = await Promise.all([
        modelService.getModelConfigs(),
        credentialService.getCredentials(),
      ]);

      modelStore.modelConfigs = modelsData;
      credentialStore.credentials = credentialsData;
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: '加载失败',
        message: error.response?.data?.detail || '无法加载数据',
      });
    } finally {
      modelStore.isLoading = false;
    }
  };

  const loadAvailableModels = async (credentialId: string) => {
    if (!credentialId) {
      setAvailableModels([]);
      return;
    }

    setLoadingModels(true);
    try {
      const response = await credentialService.getAvailableModels(credentialId);
      setAvailableModels(response.models);
    } catch (error: any) {
      console.error('Failed to load available models:', error);
      setAvailableModels([]);
      addNotification({
        type: 'error',
        title: '获取模型失败',
        message: error.response?.data?.detail || '无法获取可用模型',
      });
    } finally {
      setLoadingModels(false);
    }
  };

  const handleCredentialChange = async (credentialId: string) => {
    setFormData({ ...formData, credential_id: credentialId, model_name: '' });
    await loadAvailableModels(credentialId);
  };

  const handleCreate = () => {
    setEditingModel(null);
    setFormData({
      credential_id: '',
      model_name: '',
      target_format: 'openai',
      is_enabled: true,
      rate_limit: 100,
    });
    setErrors({});
    setAvailableModels([]);
    setOpen(true);
  };

  const handleEdit = async (model: any) => {
    setEditingModel(model);
    setFormData({
      credential_id: model.credential_id,
      model_name: model.model_name,
      target_format: model.target_format,
      is_enabled: model.is_enabled,
      rate_limit: model.rate_limit,
    });
    setErrors({});
    setOpen(true);
    // 加载可用模型
    await loadAvailableModels(model.credential_id);
  };

  const handleSubmit = async () => {
    const newErrors: Record<string, string> = {};

    if (!formData.credential_id) {
      newErrors.credential_id = '请选择凭证';
    }
    if (!formData.model_name.trim()) {
      newErrors.model_name = '请输入模型名称';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      if (editingModel) {
        const updateData: any = {
          model_name: formData.model_name,
          target_format: formData.target_format,
          is_enabled: formData.is_enabled,
          rate_limit: formData.rate_limit,
        };

        await modelService.updateModelConfig(editingModel.id, updateData);
        addNotification({
          type: 'success',
          title: '更新成功',
          message: '模型配置已更新',
        });
      } else {
        await modelService.createModelConfig(formData);
        addNotification({
          type: 'success',
          title: '创建成功',
          message: '新模型配置已创建',
        });
      }

      setOpen(false);
      loadData();
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: editingModel ? '更新失败' : '创建失败',
        message: error.response?.data?.detail || '操作失败，请重试',
      });
    }
  };

  const handleDelete = async (model: any) => {
    if (!window.confirm(`确定要删除模型配置"${model.model_name}"吗？此操作无法撤销。`)) {
      return;
    }

    try {
      await modelService.deleteModelConfig(model.id);
      addNotification({
        type: 'success',
        title: '删除成功',
        message: '模型配置已删除',
      });
      loadData();
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: '删除失败',
        message: error.response?.data?.detail || '删除失败，请重试',
      });
    }
  };

  const handleCopyApiKey = (apiKey: string) => {
    navigator.clipboard.writeText(apiKey);
    addNotification({
      type: 'success',
      title: '已复制',
      message: 'API密钥已复制到剪贴板',
    });
  };

  const handleRegenerateKey = async (model: any) => {
    if (!window.confirm('确定要重新生成API密钥吗？旧密钥将失效。')) {
      return;
    }

    try {
      const result = await modelService.regenerateProxyKey(model.id);
      addNotification({
        type: 'success',
        title: '重新生成成功',
        message: '新的API密钥已生成',
      });
      loadData();
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: '生成失败',
        message: error.response?.data?.detail || '重新生成失败，请重试',
      });
    }
  };

  const getFormatName = (format: TargetFormat) => {
    switch (format) {
      case 'openai':
        return 'OpenAI';
      case 'anthropic':
        return 'Anthropic';
      default:
        return format.toUpperCase();
    }
  };

  const validatedCredentials = credentials.filter(c => c.is_validated && c.is_active);

  if (isLoading) {
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
          模型配置
        </Typography>
        <Box display="flex" gap={1}>
          <IconButton onClick={loadData} color="primary">
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            disabled={validatedCredentials.length === 0}
          >
            添加模型配置
          </Button>
        </Box>
      </Box>

      {validatedCredentials.length === 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          请先添加并验证至少一个凭证才能配置模型转发。
        </Alert>
      )}

      {modelConfigs.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" color="textSecondary" gutterBottom>
              暂无模型配置
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={3}>
              请配置模型转发规则以开始使用LLM代理服务
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreate}
              disabled={validatedCredentials.length === 0}
            >
              添加第一个模型配置
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {modelConfigs.map((model) => (
            <Grid item xs={12} lg={6} key={model.id}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Typography variant="h6" component="h2">
                      {model.model_name}
                    </Typography>
                    <Chip
                      label={model.is_enabled ? '启用' : '禁用'}
                      color={model.is_enabled ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>

                  <Box display="flex" gap={1} mb={2}>
                    <Chip
                      label={`${model.credential_provider.toUpperCase()} → ${getFormatName(model.target_format)}`}
                      color="primary"
                      size="small"
                    />
                    <Chip
                      label={`${model.rate_limit}/分钟`}
                      variant="outlined"
                      size="small"
                    />
                  </Box>

                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    凭证: {model.credential_name}
                  </Typography>

                  <Box display="flex" alignItems="center" gap={1} mt={2}>
                    <Typography variant="body2" color="textSecondary">
                      代理密钥:
                    </Typography>
                    <Box
                      sx={{
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        bgcolor: 'grey.100',
                        p: 0.5,
                        borderRadius: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        maxWidth: '200px',
                      }}
                    >
                      {model.proxy_api_key.substring(0, 8)}...
                    </Box>
                    <Tooltip title="复制API密钥">
                      <IconButton
                        size="small"
                        onClick={() => handleCopyApiKey(model.proxy_api_key)}
                      >
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>

                  <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                    创建时间: {new Date(model.created_at).toLocaleString()}
                  </Typography>
                </CardContent>

                <CardActions>
                  <Tooltip title="重新生成密钥">
                    <IconButton
                      size="small"
                      onClick={() => handleRegenerateKey(model)}
                    >
                      <KeyIcon />
                    </IconButton>
                  </Tooltip>
                  <IconButton
                    size="small"
                    onClick={() => handleEdit(model)}
                    title="编辑配置"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(model)}
                    color="error"
                    title="删除配置"
                  >
                    <DeleteIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* 创建/编辑对话框 */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingModel ? '编辑模型配置' : '添加模型配置'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <FormControl fullWidth error={!!errors.credential_id}>
              <InputLabel>选择凭证</InputLabel>
              <Select
                value={formData.credential_id}
                onChange={(e) => handleCredentialChange(e.target.value)}
                label="选择凭证"
                disabled={!!editingModel}
              >
                {validatedCredentials.map((credential) => (
                  <MenuItem key={credential.id} value={credential.id}>
                    {credential.name} ({credential.provider.toUpperCase()})
                  </MenuItem>
                ))}
              </Select>
              {errors.credential_id && (
                <Typography variant="caption" color="error">
                  {errors.credential_id}
                </Typography>
              )}
            </FormControl>

            <FormControl fullWidth error={!!errors.model_name}>
              <InputLabel>模型名称</InputLabel>
              <Select
                value={formData.model_name}
                onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                label="模型名称"
                disabled={!formData.credential_id || loadingModels}
              >
                {loadingModels ? (
                  <MenuItem disabled>
                    <CircularProgress size={20} /> 正在加载模型...
                  </MenuItem>
                ) : availableModels.length === 0 ? (
                  <MenuItem disabled>
                    {formData.credential_id ? '无可用模型' : '请先选择凭证'}
                  </MenuItem>
                ) : (
                  availableModels.map((model) => (
                    <MenuItem key={model} value={model}>
                      {model}
                    </MenuItem>
                  ))
                )}
              </Select>
              {errors.model_name && (
                <Typography variant="caption" color="error">
                  {errors.model_name}
                </Typography>
              )}
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>目标格式</InputLabel>
              <Select
                value={formData.target_format}
                onChange={(e) => setFormData({ ...formData, target_format: e.target.value as TargetFormat })}
                label="目标格式"
              >
                <MenuItem value="openai">OpenAI格式</MenuItem>
                <MenuItem value="anthropic">Anthropic格式</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="速率限制（每分钟）"
              type="number"
              value={formData.rate_limit}
              onChange={(e) => setFormData({ ...formData, rate_limit: parseInt(e.target.value) || 100 })}
              inputProps={{ min: 1, max: 10000 }}
              fullWidth
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_enabled}
                  onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                />
              }
              label="启用此配置"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingModel ? '更新' : '创建'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Models;