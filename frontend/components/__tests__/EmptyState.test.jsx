import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Users } from 'lucide-react';
import EmptyState from '../EmptyState.jsx';

describe('EmptyState Component', () => {
     it('renders with basic props', () => {
          render(
               <EmptyState
                    icon={Users}
                    title="No Data Found"
                    description="There is no data to display"
               />
          );

          expect(screen.getByText('No Data Found')).toBeInTheDocument();
          expect(screen.getByText('There is no data to display')).toBeInTheDocument();
     });

     it('renders with action button when provided', () => {
          const mockAction = vi.fn();
          
          render(
               <EmptyState
                    icon={Users}
                    title="No Users"
                    description="No users found"
                    actionText="Create User"
                    onAction={mockAction}
               />
          );

          const button = screen.getByText('Create User');
          expect(button).toBeInTheDocument();
          
          fireEvent.click(button);
          expect(mockAction).toHaveBeenCalledTimes(1);
     });

     it('does not render action button when not provided', () => {
          render(
               <EmptyState
                    icon={Users}
                    title="No Data"
                    description="No data available"
               />
          );

          expect(screen.queryByRole('button')).not.toBeInTheDocument();
     });

     it('applies custom className', () => {
          const { container } = render(
               <EmptyState
                    icon={Users}
                    title="Test"
                    description="Test description"
                    className="custom-class"
               />
          );

          expect(container.firstChild).toHaveClass('custom-class');
     });

     it('renders without icon when not provided', () => {
          render(
               <EmptyState
                    title="No Icon"
                    description="This has no icon"
               />
          );

          expect(screen.getByText('No Icon')).toBeInTheDocument();
          expect(screen.getByText('This has no icon')).toBeInTheDocument();
     });
});