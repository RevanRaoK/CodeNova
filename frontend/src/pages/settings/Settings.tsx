import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Switch, 
  FormControlLabel, 
  TextField, 
  Button, 
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Avatar,
  InputAdornment,
} from '@mui/material';
import {
  DarkMode as DarkModeIcon,
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  Language as LanguageIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
} from '@mui/icons-material';

export const SettingsPage: React.FC = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [language, setLanguage] = useState('en');

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Account
        </Typography>
        <List>
          <ListItem>
            <ListItemText 
              primary="Profile Information" 
              secondary="Update your name, email, and other account details" 
            />
            <IconButton edge="end" aria-label="edit">
              <EditIcon />
            </IconButton>
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Change Password" 
              secondary="Update your password" 
            />
            <IconButton edge="end" aria-label="edit">
              <LockIcon />
            </IconButton>
          </ListItem>
        </List>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Preferences
        </Typography>
        <List>
          <ListItem>
            <ListItemText 
              primary="Dark Mode" 
              secondary="Switch between light and dark theme" 
            />
            <ListItemSecondaryAction>
              <Switch
                edge="end"
                checked={darkMode}
                onChange={() => setDarkMode(!darkMode)}
                inputProps={{ 'aria-labelledby': 'dark-mode-switch' }}
              />
            </ListItemSecondaryAction>
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Notifications" 
              secondary="Enable or disable notifications" 
            />
            <ListItemSecondaryAction>
              <Switch
                edge="end"
                checked={notifications}
                onChange={() => setNotifications(!notifications)}
                inputProps={{ 'aria-labelledby': 'notifications-switch' }}
              />
            </ListItemSecondaryAction>
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Email Notifications" 
              secondary="Receive email notifications" 
            />
            <ListItemSecondaryAction>
              <Switch
                edge="end"
                checked={emailNotifications}
                onChange={() => setEmailNotifications(!emailNotifications)}
                inputProps={{ 'aria-labelledby': 'email-notifications-switch' }}
              />
            </ListItemSecondaryAction>
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Language" 
              secondary="Select your preferred language" 
            />
            <ListItemSecondaryAction>
              <TextField
                select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                variant="standard"
                SelectProps={{
                  native: true,
                }}
                sx={{ minWidth: 120 }}
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
              </TextField>
            </ListItemSecondaryAction>
          </ListItem>
        </List>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom color="error">
          Danger Zone
        </Typography>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => {
            if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
              // Handle account deletion
            }
          }}
        >
          Delete Account
        </Button>
      </Paper>
    </Box>
  );
};

export default SettingsPage;
