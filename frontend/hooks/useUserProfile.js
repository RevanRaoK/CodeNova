import { useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import userService from '../services/userService';
import { useNotification } from '../contexts/NotificationContext';

/**
 * Custom hook for managing user profile data with optimistic updates
 */
export const useUserProfile = () => {
     const { user, setUser } = useAuth();
     const { showSuccess, showError } = useNotification();
     const [isLoading, setIsLoading] = useState(false);
     const [isSaving, setIsSaving] = useState(false);

     // Store original data for rollback on error
     const [originalData, setOriginalData] = useState(null);

     /**
      * Update user profile with optimistic updates and error rollback
      */
     const updateProfile = useCallback(async (profileData) => {
          if (!user?.id) {
               showError('User not authenticated');
               return false;
          }

          try {
               setIsSaving(true);

               // Store original data for potential rollback
               setOriginalData({ ...user });

               // Optimistic update - immediately update UI
               const optimisticUser = {
                    ...user,
                    ...profileData,
                    // Handle nested properties properly
                    firstName: profileData.firstName ?? user.firstName,
                    lastName: profileData.lastName ?? user.lastName,
                    email: profileData.email ?? user.email,
                    jobTitle: profileData.jobTitle ?? user.jobTitle,
                    bio: profileData.bio ?? user.bio,
                    programmingLanguages: profileData.programmingLanguages ?? user.programmingLanguages,
               };

               setUser(optimisticUser);

               // Make API call
               const updatedProfile = await userService.updateUserProfile(user.id, profileData);

               // Update with actual server response
               const serverUser = {
                    ...user,
                    ...updatedProfile,
               };

               setUser(serverUser);
               showSuccess('Profile updated successfully');

               // Clear original data since update was successful
               setOriginalData(null);

               return true;
          } catch (error) {
               console.error('Error updating profile:', error);

               // Rollback optimistic update on error
               if (originalData) {
                    setUser(originalData);
                    setOriginalData(null);
               }

               showError(error.message || 'Failed to update profile');
               return false;
          } finally {
               setIsSaving(false);
          }
     }, [user, setUser, showSuccess, showError]);

     /**
      * Update user preferences with optimistic updates
      */
     const updatePreferences = useCallback(async (preferences) => {
          if (!user?.id) {
               showError('User not authenticated');
               return false;
          }

          try {
               setIsSaving(true);

               // Store original preferences for rollback
               setOriginalData({ preferences: user.preferences });

               // Optimistic update
               const optimisticUser = {
                    ...user,
                    preferences: {
                         ...user.preferences,
                         ...preferences,
                    },
               };

               setUser(optimisticUser);

               // Make API call
               const updatedPreferences = await userService.updateUserPreferences(user.id, preferences);

               // Update with server response
               const serverUser = {
                    ...user,
                    preferences: updatedPreferences,
               };

               setUser(serverUser);
               showSuccess('Preferences updated successfully');

               setOriginalData(null);
               return true;
          } catch (error) {
               console.error('Error updating preferences:', error);

               // Rollback on error
               if (originalData?.preferences) {
                    setUser({
                         ...user,
                         preferences: originalData.preferences,
                    });
                    setOriginalData(null);
               }

               showError(error.message || 'Failed to update preferences');
               return false;
          } finally {
               setIsSaving(false);
          }
     }, [user, setUser, showSuccess, showError]);

     /**
      * Update notification preferences
      */
     const updateNotificationPreferences = useCallback(async (notificationPrefs) => {
          if (!user?.id) {
               showError('User not authenticated');
               return false;
          }

          try {
               setIsSaving(true);

               // Store original for rollback
               setOriginalData({ notificationPreferences: user.notificationPreferences });

               // Optimistic update
               const optimisticUser = {
                    ...user,
                    notificationPreferences: {
                         ...user.notificationPreferences,
                         ...notificationPrefs,
                    },
               };

               setUser(optimisticUser);

               // API call
               const updatedPrefs = await userService.updateNotificationPreferences(user.id, notificationPrefs);

               // Update with server response
               const serverUser = {
                    ...user,
                    notificationPreferences: updatedPrefs,
               };

               setUser(serverUser);
               showSuccess('Notification preferences updated successfully');

               setOriginalData(null);
               return true;
          } catch (error) {
               console.error('Error updating notification preferences:', error);

               // Rollback on error
               if (originalData?.notificationPreferences) {
                    setUser({
                         ...user,
                         notificationPreferences: originalData.notificationPreferences,
                    });
                    setOriginalData(null);
               }

               showError(error.message || 'Failed to update notification preferences');
               return false;
          } finally {
               setIsSaving(false);
          }
     }, [user, setUser, showSuccess, showError]);

     /**
      * Upload profile picture with optimistic updates
      */
     const uploadProfilePicture = useCallback(async (file) => {
          if (!user?.id) {
               showError('User not authenticated');
               return false;
          }

          try {
               setIsSaving(true);

               // Store original profile picture for rollback
               setOriginalData({ profilePictureUrl: user.profilePictureUrl });

               // Create optimistic preview
               const previewUrl = URL.createObjectURL(file);
               const optimisticUser = {
                    ...user,
                    profilePictureUrl: previewUrl,
               };

               setUser(optimisticUser);

               // Upload file
               const uploadedUrl = await userService.uploadProfilePicture(user.id, file);

               // Clean up preview URL
               URL.revokeObjectURL(previewUrl);

               // Update with actual uploaded URL
               const serverUser = {
                    ...user,
                    profilePictureUrl: uploadedUrl,
               };

               setUser(serverUser);
               showSuccess('Profile picture updated successfully');

               setOriginalData(null);
               return uploadedUrl;
          } catch (error) {
               console.error('Error uploading profile picture:', error);

               // Rollback on error
               if (originalData?.profilePictureUrl !== undefined) {
                    setUser({
                         ...user,
                         profilePictureUrl: originalData.profilePictureUrl,
                    });
                    setOriginalData(null);
               }

               showError(error.message || 'Failed to upload profile picture');
               return false;
          } finally {
               setIsSaving(false);
          }
     }, [user, setUser, showSuccess, showError]);

     /**
      * Load fresh user data from server
      */
     const refreshUserData = useCallback(async () => {
          if (!user?.id) return false;

          try {
               setIsLoading(true);

               const [profileData, preferencesData] = await Promise.all([
                    userService.getUserProfile(user.id),
                    userService.getUserPreferences(user.id).catch(() => null), // Don't fail if preferences don't exist
               ]);

               const refreshedUser = {
                    ...user,
                    ...profileData,
                    preferences: preferencesData || user.preferences,
               };

               setUser(refreshedUser);
               return true;
          } catch (error) {
               console.error('Error refreshing user data:', error);
               showError('Failed to refresh user data');
               return false;
          } finally {
               setIsLoading(false);
          }
     }, [user, setUser, showError]);

     /**
      * Update security settings
      */
     const updateSecuritySettings = useCallback(async (securitySettings) => {
          if (!user?.id) {
               showError('User not authenticated');
               return false;
          }

          try {
               setIsSaving(true);

               // Store original for rollback
               setOriginalData({ securitySettings: user.securitySettings });

               // Optimistic update
               const optimisticUser = {
                    ...user,
                    securitySettings: {
                         ...user.securitySettings,
                         ...securitySettings,
                    },
               };

               setUser(optimisticUser);

               // API call
               const updatedSettings = await userService.updateSecuritySettings(user.id, securitySettings);

               // Update with server response
               const serverUser = {
                    ...user,
                    securitySettings: updatedSettings,
               };

               setUser(serverUser);
               showSuccess('Security settings updated successfully');

               setOriginalData(null);
               return true;
          } catch (error) {
               console.error('Error updating security settings:', error);

               // Rollback on error
               if (originalData?.securitySettings) {
                    setUser({
                         ...user,
                         securitySettings: originalData.securitySettings,
                    });
                    setOriginalData(null);
               }

               showError(error.message || 'Failed to update security settings');
               return false;
          } finally {
               setIsSaving(false);
          }
     }, [user, setUser, showSuccess, showError]);

     /**
      * Delete profile picture
      */
     const deleteProfilePicture = useCallback(async () => {
          if (!user?.id) {
               showError('User not authenticated');
               return false;
          }

          try {
               setIsSaving(true);

               // Store original profile picture for rollback
               setOriginalData({ profilePictureUrl: user.profilePictureUrl });

               // Optimistic update - remove profile picture immediately
               const optimisticUser = {
                    ...user,
                    profilePictureUrl: null,
               };

               setUser(optimisticUser);

               // Make API call
               await userService.deleteProfilePicture(user.id);

               // Update with server response
               const serverUser = {
                    ...user,
                    profilePictureUrl: null,
               };

               setUser(serverUser);
               showSuccess('Profile picture deleted successfully');

               setOriginalData(null);
               return true;
          } catch (error) {
               console.error('Error deleting profile picture:', error);

               // Rollback on error
               if (originalData?.profilePictureUrl !== undefined) {
                    setUser({
                         ...user,
                         profilePictureUrl: originalData.profilePictureUrl,
                    });
                    setOriginalData(null);
               }

               showError(error.message || 'Failed to delete profile picture');
               return false;
          } finally {
               setIsSaving(false);
          }
     }, [user, setUser, showSuccess, showError]);

     return {
          user,
          isLoading,
          isSaving,
          updateProfile,
          updatePreferences,
          updateNotificationPreferences,
          updateSecuritySettings,
          uploadProfilePicture,
          deleteProfilePicture,
          refreshUserData,
     };
};