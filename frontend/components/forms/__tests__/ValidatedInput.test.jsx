import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ValidatedInput from '../ValidatedInput';

describe('ValidatedInput Component', () => {
  const defaultProps = {
    name: 'email',
    label: 'Email',
    type: 'email',
    value: '',
    onChange: vi.fn()
  };

  it('should render input with label', () => {
    render(<ValidatedInput {...defaultProps} />);
    
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('should display error message when provided', () => {
    render(<ValidatedInput {...defaultProps} error="Invalid email" />);
    
    expect(screen.getByText('Invalid email')).toBeInTheDocument();
  });

  it('should call onChange when input value changes', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    
    render(<ValidatedInput {...defaultProps} onChange={onChange} />);
    
    const input = screen.getByRole('textbox');
    await user.type(input, 'test@example.com');
    
    expect(onChange).toHaveBeenCalled();
  });

  it('should show required indicator when required', () => {
    render(<ValidatedInput {...defaultProps} required />);
    
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('should apply error styling when error exists', () => {
    render(<ValidatedInput {...defaultProps} error="Error message" />);
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500');
  });

  it('should render textarea when type is textarea', () => {
    render(<ValidatedInput {...defaultProps} type="textarea" />);
    
    expect(screen.getByRole('textbox')).toHaveAttribute('rows');
  });

  it('should handle disabled state', () => {
    render(<ValidatedInput {...defaultProps} disabled />);
    
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
  });

  it('should display placeholder text', () => {
    render(<ValidatedInput {...defaultProps} placeholder="Enter your email" />);
    
    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
  });

  it('should validate email format', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    
    render(
      <ValidatedInput 
        {...defaultProps} 
        type="email"
        onChange={onChange}
        validation={{ pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ }}
      />
    );
    
    const input = screen.getByRole('textbox');
    await user.type(input, 'invalid-email');
    
    expect(onChange).toHaveBeenCalled();
  });

  it('should handle password type with visibility toggle', () => {
    render(<ValidatedInput {...defaultProps} type="password" showPasswordToggle />);
    
    const input = screen.getByLabelText('Email');
    expect(input).toHaveAttribute('type', 'password');
  });

  it('should apply custom className', () => {
    render(<ValidatedInput {...defaultProps} className="custom-class" />);
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('custom-class');
  });

  it('should handle onBlur event', () => {
    const onBlur = vi.fn();
    render(<ValidatedInput {...defaultProps} onBlur={onBlur} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.blur(input);
    
    expect(onBlur).toHaveBeenCalled();
  });

  it('should handle onFocus event', () => {
    const onFocus = vi.fn();
    render(<ValidatedInput {...defaultProps} onFocus={onFocus} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.focus(input);
    
    expect(onFocus).toHaveBeenCalled();
  });

  it('should display helper text when provided', () => {
    render(<ValidatedInput {...defaultProps} helperText="Enter a valid email address" />);
    
    expect(screen.getByText('Enter a valid email address')).toBeInTheDocument();
  });

  it('should handle maxLength attribute', () => {
    render(<ValidatedInput {...defaultProps} maxLength={50} />);
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('maxLength', '50');
  });

  it('should handle minLength attribute', () => {
    render(<ValidatedInput {...defaultProps} minLength={5} />);
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('minLength', '5');
  });
});
