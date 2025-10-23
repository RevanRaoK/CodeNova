import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ValidatedForm from '../ValidatedForm';
import ValidatedInput from '../ValidatedInput';

describe('ValidatedForm Component', () => {
  it('should render form with children', () => {
    render(
      <ValidatedForm onSubmit={vi.fn()}>
        <ValidatedInput name="email" label="Email" type="email" />
        <button type="submit">Submit</button>
      </ValidatedForm>
    );
    
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
  });

  it('should call onSubmit when form is submitted', async () => {
    const onSubmit = vi.fn((e) => e.preventDefault());
    
    render(
      <ValidatedForm onSubmit={onSubmit}>
        <ValidatedInput name="email" label="Email" type="email" value="test@example.com" onChange={vi.fn()} />
        <button type="submit">Submit</button>
      </ValidatedForm>
    );
    
    const submitButton = screen.getByRole('button', { name: 'Submit' });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalled();
    });
  });

  it('should prevent submission when validation fails', async () => {
    const onSubmit = vi.fn();
    
    render(
      <ValidatedForm onSubmit={onSubmit} validate={() => ({ email: 'Invalid email' })}>
        <ValidatedInput name="email" label="Email" type="email" value="" onChange={vi.fn()} />
        <button type="submit">Submit</button>
      </ValidatedForm>
    );
    
    const submitButton = screen.getByRole('button', { name: 'Submit' });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  it('should display validation errors', async () => {
    const validate = () => ({ email: 'Email is required' });
    
    render(
      <ValidatedForm onSubmit={vi.fn()} validate={validate}>
        <ValidatedInput name="email" label="Email" type="email" value="" onChange={vi.fn()} />
        <button type="submit">Submit</button>
      </ValidatedForm>
    );
    
    const submitButton = screen.getByRole('button', { name: 'Submit' });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument();
    });
  });

  it('should handle form reset', () => {
    const { container } = render(
      <ValidatedForm onSubmit={vi.fn()}>
        <ValidatedInput name="email" label="Email" type="email" value="test@example.com" onChange={vi.fn()} />
        <button type="reset">Reset</button>
      </ValidatedForm>
    );
    
    const resetButton = screen.getByRole('button', { name: 'Reset' });
    fireEvent.click(resetButton);
    
    const form = container.querySelector('form');
    expect(form).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <ValidatedForm onSubmit={vi.fn()} className="custom-form">
        <button type="submit">Submit</button>
      </ValidatedForm>
    );
    
    const form = container.querySelector('form');
    expect(form).toHaveClass('custom-form');
  });

  it('should handle disabled state', () => {
    render(
      <ValidatedForm onSubmit={vi.fn()} disabled>
        <ValidatedInput name="email" label="Email" type="email" value="" onChange={vi.fn()} />
        <button type="submit">Submit</button>
      </ValidatedForm>
    );
    
    const submitButton = screen.getByRole('button', { name: 'Submit' });
    expect(submitButton).toBeDisabled();
  });

  it('should show loading state during submission', async () => {
    const onSubmit = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    render(
      <ValidatedForm onSubmit={onSubmit}>
        <ValidatedInput name="email" label="Email" type="email" value="test@example.com" onChange={vi.fn()} />
        <button type="submit">Submit</button>
      </ValidatedForm>
    );
    
    const submitButton = screen.getByRole('button', { name: 'Submit' });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });
});
