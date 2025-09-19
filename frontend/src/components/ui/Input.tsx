import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import { cva, type VariantProps } from 'class-variance-authority';
import { Icon, type IconName } from './Icon';

const inputVariants = cva(
  'flex w-full rounded-md border bg-white px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-slate-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-900 dark:ring-offset-slate-900 dark:placeholder:text-slate-400',
  {
    variants: {
      variant: {
        default: 'border-slate-200 focus-visible:ring-blue-500 dark:border-slate-700',
        error: 'border-red-300 focus-visible:ring-red-500 dark:border-red-700',
        success: 'border-green-300 focus-visible:ring-green-500 dark:border-green-700',
      },
      size: {
        sm: 'h-8 px-2 text-xs',
        md: 'h-9 px-3',
        lg: 'h-10 px-4',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputVariants> {
  leftIcon?: IconName;
  rightIcon?: IconName;
  error?: string;
  label?: string;
  helperText?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className, 
    variant, 
    size, 
    type = 'text',
    leftIcon,
    rightIcon,
    error,
    label,
    helperText,
    id,
    ...props 
  }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = Boolean(error);
    const finalVariant = hasError ? 'error' : variant;

    return (
      <div className="w-full">
        {label && (
          <label 
            htmlFor={inputId}
            className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Icon 
                name={leftIcon} 
                size="sm" 
                className="text-slate-400 dark:text-slate-500" 
              />
            </div>
          )}
          <input
            type={type}
            className={clsx(
              inputVariants({ variant: finalVariant, size }),
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              className
            )}
            ref={ref}
            id={inputId}
            {...props}
          />
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <Icon 
                name={rightIcon} 
                size="sm" 
                className="text-slate-400 dark:text-slate-500" 
              />
            </div>
          )}
        </div>
        {(error || helperText) && (
          <p className={clsx(
            'mt-1 text-xs',
            hasError 
              ? 'text-red-600 dark:text-red-400' 
              : 'text-slate-500 dark:text-slate-400'
          )}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input, inputVariants };