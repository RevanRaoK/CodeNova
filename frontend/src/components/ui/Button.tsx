import { forwardRef } from 'react';
import { clsx } from 'clsx';
import { cva, type VariantProps } from 'class-variance-authority';
import { Icon, type IconName } from './Icon';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500',
        secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-200 focus-visible:ring-slate-500 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700',
        outline: 'border border-slate-200 bg-white hover:bg-slate-50 hover:text-slate-900 focus-visible:ring-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800 dark:hover:text-slate-100',
        ghost: 'hover:bg-slate-100 hover:text-slate-900 focus-visible:ring-slate-500 dark:hover:bg-slate-800 dark:hover:text-slate-100',
        destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500',
        success: 'bg-green-600 text-white hover:bg-green-700 focus-visible:ring-green-500',
        warning: 'bg-yellow-600 text-white hover:bg-yellow-700 focus-visible:ring-yellow-500',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-9 px-4 py-2',
        lg: 'h-10 px-6',
        xl: 'h-11 px-8',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  leftIcon?: IconName;
  rightIcon?: IconName;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    asChild = false, 
    loading = false,
    leftIcon,
    rightIcon,
    children,
    disabled,
    ...props 
  }, ref) => {
    const isDisabled = disabled || loading;

    return (
      <button
        className={clsx(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={isDisabled}
        {...props}
      >
        {loading && (
          <Icon 
            name="refresh" 
            size={size === 'sm' ? 'xs' : 'sm'} 
            className="mr-2 animate-spin" 
          />
        )}
        {!loading && leftIcon && (
          <Icon 
            name={leftIcon} 
            size={size === 'sm' ? 'xs' : 'sm'} 
            className="mr-2" 
          />
        )}
        {children}
        {rightIcon && (
          <Icon 
            name={rightIcon} 
            size={size === 'sm' ? 'xs' : 'sm'} 
            className="ml-2" 
          />
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };