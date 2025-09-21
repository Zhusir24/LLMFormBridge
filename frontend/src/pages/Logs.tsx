import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
} from '@mui/material';

const Logs: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        请求日志
      </Typography>

      <Card>
        <CardContent>
          <Alert severity="info">
            日志功能正在开发中，敬请期待...
          </Alert>
          <Typography variant="body2" color="textSecondary" mt={2}>
            未来版本将提供详细的请求日志、统计信息和性能监控功能。
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Logs;