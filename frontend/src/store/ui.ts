import { proxy } from 'valtio';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    title: string;
    message?: string;
    duration?: number;
  }>;
}

export const uiStore = proxy<UIState>({
  sidebarOpen: true,
  theme: 'light',
  notifications: [],
});

// 添加通知
export const addNotification = (notification: Omit<UIState['notifications'][0], 'id'>) => {
  const id = Date.now().toString();
  uiStore.notifications.push({
    id,
    duration: 5000,
    ...notification,
  });

  // 自动移除通知
  if (notification.duration !== 0) {
    setTimeout(() => {
      removeNotification(id);
    }, notification.duration || 5000);
  }
};

// 移除通知
export const removeNotification = (id: string) => {
  const index = uiStore.notifications.findIndex(n => n.id === id);
  if (index > -1) {
    uiStore.notifications.splice(index, 1);
  }
};

// 切换侧边栏
export const toggleSidebar = () => {
  uiStore.sidebarOpen = !uiStore.sidebarOpen;
};

// 切换主题
export const toggleTheme = () => {
  uiStore.theme = uiStore.theme === 'light' ? 'dark' : 'light';
};