import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ErrorDisplay from '../ErrorDisplay';

describe('ErrorDisplay Component', () => {
  it('should not render when no error is provided', () => {
    const { container } = render(<ErrorDisplay />);
    expect(container.firstChild).toBeNull();
  });

  it('should render error message when string error is provided', () => {
    render(<ErrorDisplay error="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('should render error message from error object', () => {
    const error = new Error('Test error message');
    render(<ErrorDisplay error={error} />);
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('should render error with custom title', () => {
    render(<ErrorDisplay error="Error occurred" title="Custom Error" />);
    expect(screen.getByText('Custom Error')).toBeInTheDocument();
    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });

  it('should apply error styling', () => {
    const { container } = render(<ErrorDisplay error="Error message" />);
    const errorDiv = container.firstChild;
    expect(errorDiv).toHaveClass('text-red-600');
  });

  it('should render multiple errors as list', () => {
    const errors = ['Error 1', 'Error 2', 'Error 3'];
    render(<ErrorDisplay error={errors} />);
    
    errors.forEach(error => {
      expect(screen.getByText(error)).toBeInTheDocument();
    });
  });

  it('should handle error object with detail property', () => {
    const error = { detail: 'Detailed error message' };
    render(<ErrorDisplay error={error} />);
    expect(screen.getByText('Detailed error message')).toBeInTheDocument();
  });

  it('should handle error object with message property', () => {
    const error = { message: 'Error message from object' };
    render(<ErrorDisplay error={error} />);
    expect(screen.getByText('Error message from object')).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(<ErrorDisplay error="Error" className="custom-error" />);
    expect(container.firstChild).toHaveClass('custom-error');
  });

  it('should render with icon when showIcon is true', () => {
    const { container } = render(<ErrorDisplay error="Error" showIcon />);
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('should handle dismissible errors', () => {
    const onDismiss = vi.fn();
    render(<ErrorDisplay error="Error" dismissible onDismiss={onDismiss} />);
    
    const dismissButton = screen.getByRole('button');
    dismissButton.click();
    
    expect(onDismiss).toHaveBeenCalled();
  });
});
