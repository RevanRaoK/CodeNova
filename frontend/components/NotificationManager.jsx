import React from 'react';
import { useNotification } from '../contexts/NotificationContext';
import ToastContainer from './ToastContainer';
import ConfirmationDialog from './ConfirmationDialog';

const NotificationManager = () => {
  const { confirmDialog, closeConfirmation } = useNotification();

  return (
    <>
      <ToastContainer />
      {confirmDialog && (
        <ConfirmationDialog
          dialog={confirmDialog}
          onConfirm={confirmDialog.onConfirm}
          onCancel={confirmDialog.onCancel}
        />
      )}
    </>
  );
};

export default NotificationManager;