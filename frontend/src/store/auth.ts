import { proxy } from 'valtio';
import { AuthState } from '../types/auth';

const initialToken = localStorage.getItem('token');

export const authStore = proxy<AuthState>({
  user: null,
  token: initialToken,
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: !!initialToken,
  isLoading: false,
});

// 监听token变化并同步到localStorage
import { subscribe } from 'valtio';

subscribe(authStore, () => {
  if (authStore.token) {
    localStorage.setItem('token', authStore.token);
  } else {
    localStorage.removeItem('token');
  }

  if (authStore.refreshToken) {
    localStorage.setItem('refreshToken', authStore.refreshToken);
  } else {
    localStorage.removeItem('refreshToken');
  }
});