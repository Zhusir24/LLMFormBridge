export type Provider = 'openai' | 'anthropic' | 'claude_code' | 'gemini' | 'ernie' | 'qwen' | 'azure_openai';

export interface ModelValidationResult {
  is_valid: boolean;
  error?: string;
  validated_at: string;
}

export interface Credential {
  id: string;
  user_id: string;
  name: string;
  provider: Provider;
  api_url?: string;
  custom_models: string[];
  model_validation_results?: Record<string, ModelValidationResult>;
  is_active: boolean;
  is_validated: boolean;
  validation_error?: string;
  created_at: string;
  updated_at: string;
  api_key_masked: string;
}

export interface CredentialCreate {
  name: string;
  provider: Provider;
  api_key: string;
  api_url?: string;
  custom_models?: string[];
}

export interface CredentialUpdate {
  name?: string;
  api_key?: string;
  api_url?: string;
  custom_models?: string[];
  is_active?: boolean;
}

export interface CredentialValidation {
  is_valid: boolean;
  error_message?: string;
  available_models?: string[];
  failed_models?: string[];
  model_validation_results?: Record<string, ModelValidationResult>;
  total_models_tested?: number;
  validation_summary?: string;
}

export interface CredentialState {
  credentials: Credential[];
  selectedCredential: Credential | null;
  isLoading: boolean;
  validationStatus: Record<string, boolean>;
}