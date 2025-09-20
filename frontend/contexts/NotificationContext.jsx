import React, { createContext, useContext, useState, useCallback } from 'react';

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [confirmDialog, setConfirmDialog] = useState(null);

  // Generate unique ID for notifications
  const generateId = () => Date.now() + Math.random();

  // Add a toast notification
  const addNotification = useCallback((notification) => {
    const id = generateId();
    const newNotification = {
      id,
      type: 'info', // default type
      duration: 5000, // default duration
      ...notification,
      timestamp: Date.now()
    };

    setNotifications(prev => [...prev, newNotification]);

    // Auto-remove notification after duration (unless it's persistent)
    if (newNotification.duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, newNotification.duration);
    }

    return id;
  }, []);

  // Remove a specific notification
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  // Clear all notifications
  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Convenience methods for different notification types
  const showSuccess = useCallback((message, options = {}) => {
    return addNotification({
      type: 'success',
      message,
      ...options
    });
  }, [addNotification]);

  const showError = useCallback((message, options = {}) => {
    return addNotification({
      type: 'error',
      message,
      duration: 7000, // Errors stay longer
      ...options
    });
  }, [addNotification]);

  const showWarning = useCallback((message, options = {}) => {
    return addNotification({
      type: 'warning',
      message,
      ...options
    });
  }, [addNotification]);

  const showInfo = useCallback((message, options = {}) => {
    return addNotification({
      type: 'info',
      message,
      ...options
    });
  }, [addNotification]);

  // Show loading notification (persistent until manually removed)
  const showLoading = useCallback((message, options = {}) => {
    return addNotification({
      type: 'loading',
      message,
      duration: 0, // Persistent
      ...options
    });
  }, [addNotification]);

  // Show confirmation dialog
  const showConfirmation = useCallback((options) => {
    return new Promise((resolve) => {
      const dialog = {
        id: generateId(),
        title: 'Confirm Action',
        message: 'Are you sure you want to proceed?',
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        type: 'warning',
        ...options,
        onConfirm: () => {
          setConfirmDialog(null);
          resolve(true);
        },
        onCancel: () => {
          setConfirmDialog(null);
          resolve(false);
        }
      };
      setConfirmDialog(dialog);
    });
  }, []);

  // Close confirmation dialog
  const closeConfirmation = useCallback(() => {
    setConfirmDialog(null);
  }, []);

  const value = {
    notifications,
    confirmDialog,
    addNotification,
    removeNotification,
    clearNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading,
    showConfirmation,
    closeConfirmation
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};