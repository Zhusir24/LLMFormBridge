import React from 'react';
import { useSnapshot } from 'valtio';
import { Snackbar, Alert, AlertTitle } from '@mui/material';
import { uiStore, removeNotification } from '../../store/ui';

const NotificationManager: React.FC = () => {
  const { notifications } = useSnapshot(uiStore);

  return (
    <>
      {notifications.map((notification, index) => (
        <Snackbar
          key={notification.id}
          open={true}
          autoHideDuration={notification.duration}
          onClose={() => removeNotification(notification.id)}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ mt: index * 7 }} // 多个通知时堆叠显示
        >
          <Alert
            onClose={() => removeNotification(notification.id)}
            severity={notification.type}
            variant="filled"
            sx={{ width: '100%' }}
          >
            <AlertTitle>{notification.title}</AlertTitle>
            {notification.message}
          </Alert>
        </Snackbar>
      ))}
    </>
  );
};

export default NotificationManager;
