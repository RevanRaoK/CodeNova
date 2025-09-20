import React, { useEffect, useState } from 'react';
import { 
  AlertTriangle, 
  Info, 
  CheckCircle,
  XCircle
} from 'lucide-react';

const ConfirmationDialog = ({ dialog, onConfirm, onCancel }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (dialog) {
      // Trigger entrance animation
      const timer = setTimeout(() => setIsVisible(true), 10);
      return () => clearTimeout(timer);
    }
  }, [dialog]);

  if (!dialog) return null;

  const getIcon = () => {
    switch (dialog.type) {
      case 'danger':
        return <XCircle className="h-6 w-6 text-red-600" />;
      case 'success':
        return <CheckCircle className="h-6 w-6 text-green-600" />;
      case 'info':
        return <Info className="h-6 w-6 text-blue-600" />;
      default:
        return <AlertTriangle className="h-6 w-6 text-yellow-600" />;
    }
  };

  const getConfirmButtonStyle = () => {
    switch (dialog.type) {
      case 'danger':
        return 'bg-red-600 hover:bg-red-700 focus:ring-red-500';
      case 'success':
        return 'bg-green-600 hover:bg-green-700 focus:ring-green-500';
      case 'info':
        return 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500';
      default:
        return 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500';
    }
  };

  const handleConfirm = () => {
    setIsVisible(false);
    setTimeout(() => {
      onConfirm();
    }, 150);
  };

  const handleCancel = () => {
    setIsVisible(false);
    setTimeout(() => {
      onCancel();
    }, 150);
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      handleCancel();
    }
  };

  return (
    <div
      className={`
        fixed inset-0 z-50 overflow-y-auto transition-opacity duration-300
        ${isVisible ? 'opacity-100' : 'opacity-0'}
      `}
      aria-labelledby="modal-title"
      role="dialog"
      aria-modal="true"
    >
      <div
        className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"
        onClick={handleBackdropClick}
      >
        {/* Background overlay */}
        <div
          className={`
            fixed inset-0 bg-gray-500 transition-opacity duration-300
            ${isVisible ? 'bg-opacity-75' : 'bg-opacity-0'}
          `}
          aria-hidden="true"
        />

        {/* This element is to trick the browser into centering the modal contents. */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">
          &#8203;
        </span>

        {/* Modal panel */}
        <div
          className={`
            relative inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl 
            transform transition-all duration-300 sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6
            ${isVisible 
              ? 'translate-y-0 opacity-100 sm:scale-100' 
              : 'translate-y-4 opacity-0 sm:translate-y-0 sm:scale-95'
            }
          `}
        >
          <div className="sm:flex sm:items-start">
            <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-gray-100 sm:mx-0 sm:h-10 sm:w-10">
              {getIcon()}
            </div>
            <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                {dialog.title}
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  {dialog.message}
                </p>
                {dialog.details && (
                  <div className="mt-3 p-3 bg-gray-50 rounded-md">
                    <p className="text-xs text-gray-600">
                      {dialog.details}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={handleConfirm}
              className={`
                w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 
                text-base font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 
                sm:ml-3 sm:w-auto sm:text-sm transition-colors duration-200
                ${getConfirmButtonStyle()}
              `}
            >
              {dialog.confirmText}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm transition-colors duration-200"
            >
              {dialog.cancelText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationDialog;