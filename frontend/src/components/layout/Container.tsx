import { forwardRef } from 'react';
import { clsx } from 'clsx';
import { cva, type VariantProps } from 'class-variance-authority';

const containerVariants = cva(
  'mx-auto px-4 sm:px-6 lg:px-8',
  {
    variants: {
      size: {
        sm: 'max-w-2xl',
        md: 'max-w-4xl',
        lg: 'max-w-6xl',
        xl: 'max-w-7xl',
        full: 'max-w-full',
      },
      padding: {
        none: 'px-0',
        sm: 'px-4',
        md: 'px-4 sm:px-6 lg:px-8',
        lg: 'px-6 sm:px-8 lg:px-12',
      },
    },
    defaultVariants: {
      size: 'xl',
      padding: 'md',
    },
  }
);

export interface ContainerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof containerVariants> {}

const Container = forwardRef<HTMLDivElement, ContainerProps>(
  ({ className, size, padding, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx(containerVariants({ size, padding }), className)}
      {...props}
    />
  )
);

Container.displayName = 'Container';

export { Container, containerVariants };