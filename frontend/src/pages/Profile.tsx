import React from 'react';
import { Box, Typography, Paper, Avatar, Button } from '@mui/material';
import { useAuth } from '@/contexts/AuthContext';

export const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        My Profile
      </Typography>
      
      <Paper sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Avatar 
            sx={{ 
              width: 100, 
              height: 100, 
              fontSize: '2.5rem',
              mr: 3,
              bgcolor: 'primary.main'
            }}
          >
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </Avatar>
          <Box>
            <Typography variant="h5" component="h2">
              {user?.name || 'User'}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {user?.email || 'user@example.com'}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Account Information
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Member since: {new Date().toLocaleDateString()}
          </Typography>
          
          <Button 
            variant="outlined" 
            color="primary" 
            sx={{ mt: 2 }}
          >
            Edit Profile
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default ProfilePage;
