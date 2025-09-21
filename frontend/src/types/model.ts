export type TargetFormat = 'openai' | 'anthropic';

export interface ModelConfig {
  id: string;
  credential_id: string;
  model_name: string;
  target_format: TargetFormat;
  is_enabled: boolean;
  rate_limit: number;
  proxy_api_key: string;
  created_at: string;
  updated_at: string;
}

export interface ModelConfigWithCredential extends ModelConfig {
  credential_name: string;
  credential_provider: string;
}

export interface ModelConfigCreate {
  credential_id: string;
  model_name: string;
  target_format: TargetFormat;
  is_enabled?: boolean;
  rate_limit?: number;
}

export interface ModelConfigUpdate {
  model_name?: string;
  target_format?: TargetFormat;
  is_enabled?: boolean;
  rate_limit?: number;
}

export interface ModelConfigInfo {
  id: string;
  model_name: string;
  target_format: TargetFormat;
  is_enabled: boolean;
  rate_limit: number;
  proxy_api_key: string;
  created_at: string;
  updated_at: string;
  credential: {
    id: string;
    name: string;
    provider: string;
    is_validated: boolean;
  };
  proxy_endpoint: string;
}

export interface ModelState {
  modelConfigs: ModelConfigWithCredential[];
  selectedModel: ModelConfigWithCredential | null;
  isLoading: boolean;
}