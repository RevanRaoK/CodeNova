import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusIndicator from '../StatusIndicator';

describe('StatusIndicator Component', () => {
  it('should render success status', () => {
    const { container } = render(<StatusIndicator status="success" message="Success" />);
    
    expect(container.firstChild).toHaveClass('bg-green-50', 'border-green-200');
    expect(screen.getByText('Success')).toBeInTheDocument();
  });

  it('should render error status', () => {
    const { container } = render(<StatusIndicator status="error" message="Error" />);
    
    expect(container.firstChild).toHaveClass('bg-red-50', 'border-red-200');
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('should render warning status', () => {
    const { container } = render(<StatusIndicator status="warning" message="Warning" />);
    
    expect(container.firstChild).toHaveClass('bg-yellow-50', 'border-yellow-200');
    expect(screen.getByText('Warning')).toBeInTheDocument();
  });

  it('should render loading status with animation', () => {
    const { container } = render(<StatusIndicator status="loading" message="Loading" />);
    
    expect(container.firstChild).toHaveClass('bg-blue-50', 'border-blue-200');
    const icon = container.querySelector('.animate-spin');
    expect(icon).toBeInTheDocument();
  });

  it('should display status message', () => {
    render(<StatusIndicator status="success" message="Completed successfully" />);
    
    expect(screen.getByText('Completed successfully')).toBeInTheDocument();
  });

  it('should render with small size', () => {
    const { container } = render(<StatusIndicator status="success" message="Test" size="sm" />);
    
    expect(container.firstChild).toHaveClass('p-3');
  });

  it('should render with medium size', () => {
    const { container } = render(<StatusIndicator status="success" message="Test" size="md" />);
    
    expect(container.firstChild).toHaveClass('p-4');
  });

  it('should render with large size', () => {
    const { container } = render(<StatusIndicator status="success" message="Test" size="lg" />);
    
    expect(container.firstChild).toHaveClass('p-6');
  });

  it('should apply custom className', () => {
    const { container } = render(<StatusIndicator status="success" message="Test" className="custom-indicator" />);
    
    expect(container.firstChild).toHaveClass('custom-indicator');
  });

  it('should show progress bar when showProgress is true', () => {
    render(<StatusIndicator status="loading" message="Processing" showProgress progress={50} />);
    
    expect(screen.getByText('50% complete')).toBeInTheDocument();
  });

  it('should render completed status', () => {
    const { container } = render(<StatusIndicator status="completed" message="Done" />);
    
    expect(container.firstChild).toHaveClass('bg-green-50', 'border-green-200');
    expect(screen.getByText('Done')).toBeInTheDocument();
  });

  it('should render pending status', () => {
    const { container } = render(<StatusIndicator status="pending" message="Waiting" />);
    
    expect(container.firstChild).toHaveClass('bg-gray-50', 'border-gray-200');
    expect(screen.getByText('Waiting')).toBeInTheDocument();
  });

  it('should render with icon', () => {
    const { container } = render(<StatusIndicator status="success" message="Test" />);
    
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });
});
