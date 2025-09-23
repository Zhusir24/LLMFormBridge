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
  Link,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Collapse,
  Paper,
  Stack,
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
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Close as CloseIcon,
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
    custom_models: [],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [credentialModels, setCredentialModels] = useState<Record<string, string[]>>({});
  const [expandedCredentials, setExpandedCredentials] = useState<Record<string, boolean>>({});
  const [newCustomModel, setNewCustomModel] = useState('');
  const [showCustomModels, setShowCustomModels] = useState(false);

  useEffect(() => {
    loadCredentials();
  }, []);

  const loadCredentials = async () => {
    credentialStore.isLoading = true;
    try {
      const data = await credentialService.getCredentials();
      credentialStore.credentials = data;

      // 为所有已验证的凭证加载可用模型
      const validatedCredentials = data.filter(c => c.is_validated);
      await Promise.all(
        validatedCredentials.map(credential => loadCredentialModels(credential.id))
      );
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

  const loadCredentialModels = async (credentialId: string) => {
    try {
      const response = await credentialService.getAvailableModels(credentialId);
      setCredentialModels(prev => ({
        ...prev,
        [credentialId]: response.models
      }));
    } catch (error) {
      console.error('Failed to load models for credential:', credentialId, error);
    }
  };

  const toggleModelExpansion = (credentialId: string) => {
    setExpandedCredentials(prev => ({
      ...prev,
      [credentialId]: !prev[credentialId]
    }));
  };

  const handleCreate = () => {
    setEditingCredential(null);
    setFormData({
      name: '',
      provider: 'openai',
      api_key: '',
      api_url: '',
      custom_models: [],
    });
    setErrors({});
    setNewCustomModel('');
    setShowCustomModels(false);
    setOpen(true);
  };

  const handleEdit = (credential: Credential) => {
    setEditingCredential(credential);
    setFormData({
      name: credential.name,
      provider: credential.provider,
      api_key: '', // 不显示原密钥
      api_url: credential.api_url || '',
      custom_models: credential.custom_models || [],
    });
    setErrors({});
    setNewCustomModel('');
    setShowCustomModels(credential.custom_models && credential.custom_models.length > 0);
    setOpen(true);
  };

  const addCustomModel = () => {
    if (newCustomModel.trim() && !formData.custom_models?.includes(newCustomModel.trim())) {
      setFormData({
        ...formData,
        custom_models: [...(formData.custom_models || []), newCustomModel.trim()]
      });
      setNewCustomModel('');
    }
  };

  const removeCustomModel = (modelToRemove: string) => {
    setFormData({
      ...formData,
      custom_models: formData.custom_models?.filter(model => model !== modelToRemove) || []
    });
  };

  const handleCustomModelKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      addCustomModel();
    }
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
          custom_models: formData.custom_models || [],
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
        // 验证成功后加载可用模型
        await loadCredentialModels(credential.id);
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
      case 'claude_code':
        return 'Claude Code';
      default:
        return String(provider).toUpperCase();
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

                  {credential.is_validated && credentialModels[credential.id] && (
                    <Box mt={1}>
                      <Box display="flex" alignItems="center" justifyContent="space-between" mb={0.5}>
                        <Typography variant="body2" color="textSecondary">
                          支持的模型 ({credentialModels[credential.id].length}个):
                        </Typography>
                        {credentialModels[credential.id].length > 3 && (
                          <Link
                            component="button"
                            variant="caption"
                            onClick={() => toggleModelExpansion(credential.id)}
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 0.5,
                              textDecoration: 'none',
                              '&:hover': { textDecoration: 'underline' }
                            }}
                          >
                            {expandedCredentials[credential.id] ? '收起' : '查看全部'}
                            {expandedCredentials[credential.id] ? (
                              <ExpandLessIcon fontSize="small" />
                            ) : (
                              <ExpandMoreIcon fontSize="small" />
                            )}
                          </Link>
                        )}
                      </Box>
                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {(expandedCredentials[credential.id]
                          ? credentialModels[credential.id]
                          : credentialModels[credential.id].slice(0, 3)
                        ).map((model) => (
                          <Chip
                            key={model}
                            label={model}
                            size="small"
                            variant="outlined"
                            sx={{
                              fontSize: '0.7rem',
                              height: '20px',
                              '& .MuiChip-label': {
                                padding: '0 6px'
                              }
                            }}
                          />
                        ))}
                        {!expandedCredentials[credential.id] && credentialModels[credential.id].length > 3 && (
                          <Chip
                            label={`+${credentialModels[credential.id].length - 3}个`}
                            size="small"
                            variant="outlined"
                            sx={{
                              fontSize: '0.7rem',
                              height: '20px',
                              color: 'primary.main',
                              borderColor: 'primary.main'
                            }}
                          />
                        )}
                      </Box>
                    </Box>
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
                <MenuItem value="claude_code">Claude Code</MenuItem>
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
              placeholder={
                formData.provider === 'openai' ? 'https://api.openai.com/v1' :
                formData.provider === 'anthropic' ? 'https://api.anthropic.com/v1' :
                formData.provider === 'claude_code' ? 'https://api.claude.ai/v1' : 'https://api.openai.com/v1'
              }
              fullWidth
            />

            {/* 自定义模型设置 */}
            <Box>
              <Button
                variant="outlined"
                onClick={() => setShowCustomModels(!showCustomModels)}
                startIcon={showCustomModels ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                fullWidth
                sx={{ justifyContent: 'flex-start' }}
              >
                自定义模型列表 (可选)
              </Button>

              <Collapse in={showCustomModels}>
                <Paper sx={{ mt: 1, p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body2" color="textSecondary" mb={2}>
                    添加您要使用的自定义模型名称。如果设置了自定义模型，验证时将只测试这些模型而非默认模型列表。
                  </Typography>

                  <Stack direction="row" spacing={1} mb={2}>
                    <TextField
                      label="模型名称"
                      value={newCustomModel}
                      onChange={(e) => setNewCustomModel(e.target.value)}
                      onKeyPress={handleCustomModelKeyPress}
                      placeholder="例如: gpt-4, claude-3-opus-20240229"
                      size="small"
                      fullWidth
                    />
                    <Button
                      variant="contained"
                      onClick={addCustomModel}
                      disabled={!newCustomModel.trim()}
                      size="small"
                    >
                      添加
                    </Button>
                  </Stack>

                  {formData.custom_models && formData.custom_models.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        已添加的模型:
                      </Typography>
                      <Stack direction="row" flexWrap="wrap" gap={1}>
                        {formData.custom_models.map((model, index) => (
                          <Chip
                            key={index}
                            label={model}
                            onDelete={() => removeCustomModel(model)}
                            deleteIcon={<CloseIcon />}
                            color="primary"
                            variant="outlined"
                            size="small"
                          />
                        ))}
                      </Stack>
                    </Box>
                  )}
                </Paper>
              </Collapse>
            </Box>
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