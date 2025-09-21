export * from './auth';
export * from './credential';
export * from './model';

export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  detail?: string;
}

export interface ApiError {
  detail: string;
  status?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}