import { apiClient } from './api';
import { Credential, CredentialCreate, CredentialUpdate, CredentialValidation } from '../types/credential';

export class CredentialService {
  async getCredentials(): Promise<Credential[]> {
    return apiClient.get<Credential[]>('/credentials');
  }

  async getCredential(id: string): Promise<Credential> {
    return apiClient.get<Credential>(`/credentials/${id}`);
  }

  async createCredential(data: CredentialCreate): Promise<Credential> {
    return apiClient.post<Credential>('/credentials', data);
  }

  async updateCredential(id: string, data: CredentialUpdate): Promise<Credential> {
    return apiClient.put<Credential>(`/credentials/${id}`, data);
  }

  async deleteCredential(id: string): Promise<void> {
    return apiClient.delete(`/credentials/${id}`);
  }

  async validateCredential(id: string): Promise<CredentialValidation> {
    return apiClient.post<CredentialValidation>(`/credentials/${id}/validate`);
  }

  async getAvailableModels(id: string): Promise<{ models: string[] }> {
    return apiClient.get<{ models: string[] }>(`/credentials/${id}/models`);
  }
}

export const credentialService = new CredentialService();