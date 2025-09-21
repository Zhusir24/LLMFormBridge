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
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  CheckCircle,
  Error,
  Warning,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useSnapshot } from 'valtio';
import { credentialStore } from '../store/credentials';
import { credentialService } from '../services/credentials';
import { addNotification } from '../store/ui';
import { Credential, CredentialCreate, Provider } from '../types/credential';

const Credentials: React.FC = () => {
  const { credentials, isLoading } = useSnapshot(credentialStore);
  const [open, setOpen] = useState(false);
  const [editingCredential, setEditingCredential] = useState<Credential | null>(null);
  const [validating, setValidating] = useState<Record<string, boolean>>({});

  const [formData, setFormData] = useState<CredentialCreate>({
    name: '',
    provider: 'openai',
    api_key: '',
    api_url: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    credentialStore.isLoading = true;
    try {
      const data = await credentialService.getCredentials();
      credentialStore.credentials = data;
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: '加载失败',
        message: error.response?.data?.detail || '无法加载凭证列表',
      });
    } finally {
      credentialStore.isLoading = false;
    }
  };

  const handleCreate = () => {
    setEditingCredential(null);
    setFormData({
      name: '',
      provider: 'openai',
      api_key: '',
      api_url: '',
    });
    setErrors({});
    setOpen(true);
  };

  const handleEdit = (credential: Credential) => {
    setEditingCredential(credential);
    setFormData({
      name: credential.name,
      provider: credential.provider,
      api_key: '', // 不显示原密钥
      api_url: credential.api_url || '',
    });
    setErrors({});
    setOpen(true);
  };

  const handleSubmit = async () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = '请输入凭证名称';
    }
    if (!formData.api_key.trim() && !editingCredential) {
      newErrors.api_key = '请输入API密钥';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      if (editingCredential) {
        const updateData: any = {
          name: formData.name,
          api_url: formData.api_url || undefined,
        };
        if (formData.api_key.trim()) {
          updateData.api_key = formData.api_key;
        }

        await credentialService.updateCredential(editingCredential.id, updateData);
        addNotification({
          type: 'success',
          title: '更新成功',
          message: '凭证信息已更新',
        });
      } else {
        await credentialService.createCredential(formData);
        addNotification({
          type: 'success',
          title: '创建成功',
          message: '新凭证已创建',
        });
      }

      setOpen(false);
      loadCredentials();
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: editingCredential ? '更新失败' : '创建失败',
        message: error.response?.data?.detail || '操作失败，请重试',
      });
    }
  };

  const handleDelete = async (credential: Credential) => {
    if (!window.confirm(`确定要删除凭证"${credential.name}"吗？此操作无法撤销。`)) {
      return;
    }

    try {
      await credentialService.deleteCredential(credential.id);
      addNotification({
        type: 'success',
        title: '删除成功',
        message: '凭证已删除',
      });
      loadCredentials();
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: '删除失败',
        message: error.response?.data?.detail || '删除失败，请重试',
      });
    }
  };

  const handleValidate = async (credential: Credential) => {
    setValidating({ ...validating, [credential.id]: true });
    try {
      const result = await credentialService.validateCredential(credential.id);
      if (result.is_valid) {
        addNotification({
          type: 'success',
          title: '验证成功',
          message: `凭证"${credential.name}"验证通过`,
        });
      } else {
        addNotification({
          type: 'error',
          title: '验证失败',
          message: result.error_message || '凭证验证失败',
        });
      }
      loadCredentials();
    } catch (error: any) {
      addNotification({
        type: 'error',
        title: '验证失败',
        message: error.response?.data?.detail || '验证过程中发生错误',
      });
    } finally {
      setValidating({ ...validating, [credential.id]: false });
    }
  };

  const getStatusIcon = (credential: Credential) => {
    if (credential.is_validated) {
      return <CheckCircle color="success" />;
    } else if (credential.validation_error) {
      return <Error color="error" />;
    } else {
      return <Warning color="warning" />;
    }
  };

  const getProviderName = (provider: Provider) => {
    switch (provider) {
      case 'openai':
        return 'OpenAI';
      case 'anthropic':
        return 'Anthropic';
      default:
        return provider.toUpperCase();
    }
  };

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
          凭证管理
        </Typography>
        <Box display="flex" gap={1}>
          <IconButton onClick={loadCredentials} color="primary">
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            添加凭证
          </Button>
        </Box>
      </Box>

      {credentials.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h6" color="textSecondary" gutterBottom>
              暂无凭证
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={3}>
              请添加LLM服务提供商的API凭证以开始使用
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreate}
            >
              添加第一个凭证
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {credentials.map((credential) => (
            <Grid item xs={12} md={6} lg={4} key={credential.id}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Typography variant="h6" component="h2">
                      {credential.name}
                    </Typography>
                    {getStatusIcon(credential)}
                  </Box>

                  <Box display="flex" gap={1} mb={2}>
                    <Chip
                      label={getProviderName(credential.provider)}
                      color="primary"
                      size="small"
                    />
                    <Chip
                      label={credential.is_active ? '活跃' : '禁用'}
                      color={credential.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>

                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    API密钥: {credential.api_key_masked}
                  </Typography>

                  {credential.api_url && (
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      自定义URL: {credential.api_url}
                    </Typography>
                  )}

                  {credential.validation_error && (
                    <Alert severity="error" sx={{ mt: 1, fontSize: '0.75rem' }}>
                      {credential.validation_error}
                    </Alert>
                  )}

                  <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                    创建时间: {new Date(credential.created_at).toLocaleString()}
                  </Typography>
                </CardContent>

                <CardActions>
                  <IconButton
                    size="small"
                    onClick={() => handleValidate(credential)}
                    disabled={validating[credential.id]}
                    title="验证凭证"
                  >
                    {validating[credential.id] ? (
                      <CircularProgress size={20} />
                    ) : (
                      <VisibilityIcon />
                    )}
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleEdit(credential)}
                    title="编辑凭证"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(credential)}
                    color="error"
                    title="删除凭证"
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
          {editingCredential ? '编辑凭证' : '添加凭证'}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField
              label="凭证名称"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              error={!!errors.name}
              helperText={errors.name}
              fullWidth
            />

            <FormControl fullWidth disabled={!!editingCredential}>
              <InputLabel>服务提供商</InputLabel>
              <Select
                value={formData.provider}
                onChange={(e) => setFormData({ ...formData, provider: e.target.value as Provider })}
                label="服务提供商"
              >
                <MenuItem value="openai">OpenAI</MenuItem>
                <MenuItem value="anthropic">Anthropic</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="API密钥"
              type="password"
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              error={!!errors.api_key}
              helperText={errors.api_key || (editingCredential ? '留空则不更新密钥' : '')}
              fullWidth
            />

            <TextField
              label="自定义API URL（可选）"
              value={formData.api_url}
              onChange={(e) => setFormData({ ...formData, api_url: e.target.value })}
              placeholder={formData.provider === 'openai' ? 'https://api.openai.com/v1' : 'https://api.anthropic.com/v1'}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingCredential ? '更新' : '创建'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Credentials;