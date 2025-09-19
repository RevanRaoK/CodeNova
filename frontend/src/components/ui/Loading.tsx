import React from 'react';
import { clsx } from 'clsx';
import { Icon } from './Icon';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className 
}) => (
  <Icon 
    name="refresh" 
    className={clsx(sizeClasses[size], 'animate-spin', className)} 
  />
);

interface LoadingDotsProps {
  className?: string;
}

export const LoadingDots: React.FC<LoadingDotsProps> = ({ className }) => (
  <div className={clsx('flex space-x-1', className)}>
    <div className="h-2 w-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
    <div className="h-2 w-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
    <div className="h-2 w-2 bg-slate-400 rounded-full animate-bounce"></div>
  </div>
);

interface LoadingSkeletonProps {
  className?: string;
  lines?: number;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ 
  className, 
  lines = 1 
}) => (
  <div className={clsx('animate-pulse', className)}>
    {Array.from({ length: lines }).map((_, index) => (
      <div 
        key={index}
        className={clsx(
          'bg-slate-200 dark:bg-slate-700 rounded',
          index === lines - 1 ? 'w-3/4' : 'w-full',
          lines > 1 ? 'h-4 mb-2' : 'h-4'
        )}
      />
    ))}
  </div>
);

interface LoadingOverlayProps {
  isLoading: boolean;
  children: React.ReactNode;
  message?: string;
  className?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isLoading,
  children,
  message = 'Loading...',
  className,
}) => (
  <div className={clsx('relative', className)}>
    {children}
    {isLoading && (
      <div className="absolute inset-0 bg-white/80 dark:bg-slate-900/80 flex items-center justify-center z-10">
        <div className="flex flex-col items-center space-y-3">
          <LoadingSpinner size="lg" />
          <p className="text-sm text-slate-600 dark:text-slate-400">{message}</p>
        </div>
      </div>
    )}
  </div>
);

interface LoadingPageProps {
  message?: string;
  className?: string;
}

export const LoadingPage: React.FC<LoadingPageProps> = ({
  message = 'Loading...',
  className,
}) => (
  <div className={clsx(
    'flex flex-col items-center justify-center min-h-screen space-y-4',
    className
  )}>
    <LoadingSpinner size="xl" />
    <p className="text-lg text-slate-600 dark:text-slate-400">{message}</p>
  </div>
);

// Card skeleton for loading states
export const CardSkeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div className={clsx('bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-6', className)}>
    <div className="animate-pulse">
      <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4 mb-4"></div>
      <div className="space-y-2">
        <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded"></div>
        <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-5/6"></div>
        <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-4/6"></div>
      </div>
    </div>
  </div>
);