import { apiClient } from './api';
import { LoginRequest, RegisterRequest, TokenResponse, User } from '../types/auth';

export class AuthService {
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/login', credentials);
  }

  async register(userData: RegisterRequest): Promise<User> {
    return apiClient.post<User>('/auth/register', userData);
  }

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/auth/me');
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
  }

  async logout(): Promise<void> {
    return apiClient.post('/auth/logout');
  }
}

export const authService = new AuthService();