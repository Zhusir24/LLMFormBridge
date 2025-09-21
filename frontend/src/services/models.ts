import { apiClient } from './api';
import {
  ModelConfig,
  ModelConfigWithCredential,
  ModelConfigCreate,
  ModelConfigUpdate,
  ModelConfigInfo
} from '../types/model';

export class ModelService {
  async getModelConfigs(): Promise<ModelConfigWithCredential[]> {
    return apiClient.get<ModelConfigWithCredential[]>('/models');
  }

  async getModelConfig(id: string): Promise<ModelConfig> {
    return apiClient.get<ModelConfig>(`/models/${id}`);
  }

  async getModelConfigInfo(id: string): Promise<ModelConfigInfo> {
    return apiClient.get<ModelConfigInfo>(`/models/${id}/info`);
  }

  async createModelConfig(data: ModelConfigCreate): Promise<ModelConfig> {
    return apiClient.post<ModelConfig>('/models', data);
  }

  async updateModelConfig(id: string, data: ModelConfigUpdate): Promise<ModelConfig> {
    return apiClient.put<ModelConfig>(`/models/${id}`, data);
  }

  async deleteModelConfig(id: string): Promise<void> {
    return apiClient.delete(`/models/${id}`);
  }

  async regenerateProxyKey(id: string): Promise<{ proxy_api_key: string }> {
    return apiClient.post<{ proxy_api_key: string }>(`/models/${id}/regenerate-key`);
  }
}

export const modelService = new ModelService();