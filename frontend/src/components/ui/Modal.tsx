import React, { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { clsx } from 'clsx';
import { Icon } from './Icon';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showCloseButton?: boolean;
  closeOnOverlayClick?: boolean;
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-7xl',
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  showCloseButton = true,
  closeOnOverlayClick = true,
}) => {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog 
        as="div" 
        className="relative z-50" 
        onClose={closeOnOverlayClick ? onClose : () => {}}
      >
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25 dark:bg-opacity-50" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel 
                className={clsx(
                  'w-full transform overflow-hidden rounded-2xl bg-white dark:bg-slate-900 p-6 text-left align-middle shadow-xl transition-all',
                  sizeClasses[size]
                )}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex-1">
                    {title && (
                      <Dialog.Title
                        as="h3"
                        className="text-lg font-medium leading-6 text-slate-900 dark:text-slate-100"
                      >
                        {title}
                      </Dialog.Title>
                    )}
                    {description && (
                      <Dialog.Description className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        {description}
                      </Dialog.Description>
                    )}
                  </div>
                  {showCloseButton && (
                    <button
                      type="button"
                      className="ml-4 rounded-md text-slate-400 hover:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:hover:text-slate-300"
                      onClick={onClose}
                    >
                      <span className="sr-only">Close</span>
                      <Icon name="x-mark" size="lg" />
                    </button>
                  )}
                </div>
                
                <div className="mt-4">
                  {children}
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

// Modal compound components for better composition
export const ModalHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
  children, 
  className 
}) => (
  <div className={clsx('mb-4', className)}>
    {children}
  </div>
);

export const ModalBody: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
  children, 
  className 
}) => (
  <div className={clsx('mb-6', className)}>
    {children}
  </div>
);

export const ModalFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({ 
  children, 
  className 
}) => (
  <div className={clsx('flex justify-end space-x-3 pt-4 border-t border-slate-200 dark:border-slate-700', className)}>
    {children}
  </div>
);