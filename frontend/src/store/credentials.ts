import { proxy } from 'valtio';
import { CredentialState } from '../types/credential';

export const credentialStore = proxy<CredentialState>({
  credentials: [],
  selectedCredential: null,
  isLoading: false,
  validationStatus: {},
});