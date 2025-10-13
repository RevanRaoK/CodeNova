import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useUserProfile } from '../hooks/useUserProfile';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import userService from '../services/userService';

// Mock dependencies
vi.mock('../contexts/AuthContext');
vi.mock('../contexts/NotificationContext');
vi.mock('../services/userService');

describe('useUserProfile', () => {
     const mockUser = {
          id: '1',
          firstName: 'John',
          lastName: 'Doe',
          email: 'john@example.com'
     };

     const mockSetUser = vi.fn();
     const mockShowSuccess = vi.fn();
     const mockShowError = vi.fn();

     beforeEach(() => {
          vi.clearAllMocks();

          useAuth.mockReturnValue({
               user: mockUser,
               setUser: mockSetUser
          });

          useNotification.mockReturnValue({
               showSuccess: mockShowSuccess,
               showError: mockShowError
          });
     });

     it('should initialize with correct default values', () => {
          const { result } = renderHook(() => useUserProfile());

          expect(result.current.user).toBe(mockUser);
          expect(result.current.isLoading).toBe(false);
          expect(result.current.isSaving).toBe(false);
     });

     it('should update profile with optimistic updates', async () => {
          const profileData = { firstName: 'Jane', lastName: 'Smith' };
          userService.updateUserProfile.mockResolvedValue(profileData);

          const { result } = renderHook(() => useUserProfile());

          await act(async () => {
               const success = await result.current.updateProfile(profileData);
               expect(success).toBe(true);
          });

          expect(mockSetUser).toHaveBeenCalledWith(expect.objectContaining({
               ...mockUser,
               ...profileData
          }));
          expect(mockShowSuccess).toHaveBeenCalledWith('Profile updated successfully');
     });

     it('should handle profile update errors with rollback', async () => {
          const profileData = { firstName: 'Jane' };
          const error = new Error('Update failed');
          userService.updateUserProfile.mockRejectedValue(error);

          const { result } = renderHook(() => useUserProfile());

          await act(async () => {
               const success = await result.current.updateProfile(profileData);
               expect(success).toBe(false);
          });

          expect(mockShowError).toHaveBeenCalledWith('Update failed');
     });
});