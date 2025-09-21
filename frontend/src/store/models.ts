import { proxy } from 'valtio';
import { ModelState } from '../types/model';

export const modelStore = proxy<ModelState>({
  modelConfigs: [],
  selectedModel: null,
  isLoading: false,
});