import React, { useState, useEffect, useRef } from 'react';
import {
  UserIcon,
  MailIcon,
  KeyIcon,
  LogOutIcon,
  CameraIcon,
  SaveIcon,
  UploadIcon,
  TrashIcon,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useUserProfile } from '../hooks/useUserProfile';
import Toast from '../components/Toast';
import ValidatedForm from '../components/forms/ValidatedForm';
import ValidatedInput from '../components/forms/ValidatedInput';
import ErrorDisplay from '../components/forms/ErrorDisplay';
import { ValidationSchemas, FieldValidator } from '../utils/validation';

export function Profile() {
  const { user, logout } = useAuth();
  const { updateProfile, uploadProfilePicture, deleteProfilePicture, isSaving, refreshUserData } = useUserProfile();
  const fileInputRef = useRef(null);

  // Form state
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    jobTitle: '',
    bio: '',
    programmingLanguages: [],
  });

  // Profile picture state
  const [profilePicture, setProfilePicture] = useState(null);
  const [profilePicturePreview, setProfilePicturePreview] = useState(null);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  const [deletingPicture, setDeletingPicture] = useState(false);

  // Toast state
  const [toast, setToast] = useState(null);

  // Available programming languages
  const programmingLanguages = [
    'JavaScript',
    'TypeScript',
    'Python',
    'Java',
    'C#',
    'Go',
    'Rust',
    'PHP',
    'Ruby',
    'Swift',
  ];

  // Store original form data for reset functionality
  const [originalFormData, setOriginalFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    jobTitle: '',
    bio: '',
    programmingLanguages: [],
  });

  // Initialize form data when user data is available
  useEffect(() => {
    if (user) {
      const initialData = {
        firstName: user.firstName || user.first_name || '',
        lastName: user.lastName || user.last_name || '',
        email: user.email || '',
        jobTitle: user.jobTitle || user.job_title || '',
        bio: user.bio || '',
        programmingLanguages: Array.isArray(user.programmingLanguages) 
          ? user.programmingLanguages 
          : Array.isArray(user.programming_languages)
          ? user.programming_languages
          : [],
      };
      
      setFormData(initialData);
      setOriginalFormData(initialData);

      if (user.profilePictureUrl || user.profile_picture_url) {
        setProfilePicturePreview(
          user.profilePictureUrl || user.profile_picture_url
        );
      } else {
        setProfilePicturePreview(null);
      }
    }
  }, [user]);

  // Refresh profile data on component mount to ensure latest data
  useEffect(() => {
    const loadProfileData = async () => {
      if (user?.id) {
        setIsLoadingProfile(true);
        try {
          await refreshUserData();
        } catch (error) {
          console.error('Failed to refresh profile data:', error);
          showToast('Failed to load latest profile data', 'error');
        } finally {
          setIsLoadingProfile(false);
        }
      }
    };

    loadProfileData();
  }, []); // Only run on mount

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleLanguageToggle = (language) => {
    setFormData((prev) => ({
      ...prev,
      programmingLanguages: prev.programmingLanguages.includes(language)
        ? prev.programmingLanguages.filter((lang) => lang !== language)
        : [...prev.programmingLanguages, language],
    }));
  };

  const handleProfilePictureChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type.toLowerCase())) {
        showToast('Please select a valid image file (JPEG, PNG, GIF, or WebP)', 'error');
        e.target.value = ''; // Clear the input
        return;
      }

      // Validate file size (5MB limit)
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        showToast('Image size must be less than 5MB', 'error');
        e.target.value = ''; // Clear the input
        return;
      }

      // Validate minimum file size (1KB to avoid empty files)
      if (file.size < 1024) {
        showToast('Image file is too small. Please select a valid image.', 'error');
        e.target.value = ''; // Clear the input
        return;
      }

      setProfilePicture(file);

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setProfilePicturePreview(e.target.result);
      };
      reader.onerror = () => {
        showToast('Failed to read image file', 'error');
        setProfilePicture(null);
        setProfilePicturePreview(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleProfilePictureUpload = async () => {
    if (!profilePicture) return;

    try {
      setUploadingPicture(true);
      const uploadedUrl = await uploadProfilePicture(profilePicture);
      if (uploadedUrl) {
        setProfilePicture(null);
        setProfilePicturePreview(uploadedUrl);
        showToast('Profile picture updated successfully', 'success');
        
        // Clear the file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    } catch (error) {
      console.error('Error uploading profile picture:', error);
      showToast(error.message || 'Failed to upload profile picture', 'error');
      
      // Reset preview on error
      setProfilePicture(null);
      if (user?.profilePictureUrl || user?.profile_picture_url) {
        setProfilePicturePreview(user.profilePictureUrl || user.profile_picture_url);
      } else {
        setProfilePicturePreview(null);
      }
      
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } finally {
      setUploadingPicture(false);
    }
  };

  const handleDeleteProfilePicture = async () => {
    if (!profilePicturePreview) return;

    try {
      setDeletingPicture(true);
      const success = await deleteProfilePicture();
      if (success) {
        setProfilePicturePreview(null);
        setProfilePicture(null);
        showToast('Profile picture deleted successfully', 'success');
        
        // Clear the file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    } catch (error) {
      console.error('Error deleting profile picture:', error);
      showToast(error.message || 'Failed to delete profile picture', 'error');
    } finally {
      setDeletingPicture(false);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      const success = await updateProfile(formData);
      if (success) {
        // Update original data after successful save
        setOriginalFormData({ ...formData });
        showToast('Profile updated successfully! Your changes have been saved.', 'success');
        return success;
      }
    } catch (error) {
      console.error('Profile update error:', error);
      throw error; // Let ValidatedForm handle the error display
    }
  };

  const handleCancel = () => {
    // Reset form to last saved values
    setFormData({ ...originalFormData });
    showToast('Changes cancelled', 'info');
  };

  // Check if form has changes
  const hasChanges = () => {
    return JSON.stringify(formData) !== JSON.stringify(originalFormData);
  };

  // Create form validator
  const createFormValidator = () => {
    return ValidationSchemas.profile(formData);
  };

  const [isLoadingProfile, setIsLoadingProfile] = useState(false);

  // Warn user about unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasChanges()) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [formData, originalFormData]);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (!user || isLoadingProfile) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">
            {!user ? 'Loading user data...' : 'Refreshing profile...'}
          </p>
        </div>
      </div>
    );
  }

  const displayName =
    `${formData.firstName} ${formData.lastName}`.trim() ||
    user.username ||
    user.email;
  const memberSince = user.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
      })
    : 'Recently';

  return (
    <div className="w-full">
      <h1 className="text-2xl font-bold mb-6 text-gray-900">Profile</h1>
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden transition-colors duration-200">
        <div className="md:flex">
          {/* Left sidebar with profile info */}
          <div className="md:w-80 bg-gray-50 p-6 border-b md:border-b-0 md:border-r border-gray-200 transition-colors duration-200">
            <div className="flex flex-col items-center text-center">
              <div className="relative">
                <div className="w-32 h-32 rounded-full bg-indigo-100 flex items-center justify-center border-4 border-white shadow overflow-hidden transition-colors duration-200">
                  {profilePicturePreview ? (
                    <img
                      src={profilePicturePreview}
                      alt="Profile"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <UserIcon className="h-16 w-16 text-indigo-500" />
                  )}
                </div>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute bottom-0 right-0 bg-indigo-600 p-2 rounded-full text-white hover:bg-indigo-700 transition-colors duration-200"
                >
                  <CameraIcon className="h-4 w-4" />
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleProfilePictureChange}
                  className="hidden"
                />
              </div>

              <div className="mt-2 flex flex-col items-center space-y-2">
                {profilePicture && (
                  <button
                    onClick={handleProfilePictureUpload}
                    disabled={uploadingPicture || deletingPicture}
                    className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors duration-200"
                  >
                    {uploadingPicture ? (
                      <>
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                        Uploading...
                      </>
                    ) : (
                      <>
                        <UploadIcon className="mr-1 h-3 w-3" />
                        Upload
                      </>
                    )}
                  </button>
                )}
                
                {profilePicturePreview && !profilePicture && (
                  <button
                    onClick={handleDeleteProfilePicture}
                    disabled={deletingPicture || uploadingPicture}
                    className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors duration-200"
                  >
                    {deletingPicture ? (
                      <>
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                        Deleting...
                      </>
                    ) : (
                      <>
                        <TrashIcon className="mr-1 h-3 w-3" />
                        Delete
                      </>
                    )}
                  </button>
                )}
              </div>

              <h2 className="mt-4 text-xl font-semibold text-gray-900">
                {displayName}
              </h2>
              <p className="text-gray-500">
                {formData.jobTitle || 'Developer'}
              </p>
              <div className="mt-6 w-full">
                <div className="flex items-center py-3 border-b border-gray-200">
                  <MailIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-gray-600 text-sm">
                    {formData.email}
                  </span>
                </div>
                <div className="flex items-center py-3">
                  <KeyIcon className="h-5 w-5 text-gray-400 mr-3" />
                  <span className="text-gray-600 text-sm">
                    Member since {memberSince}
                  </span>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="mt-6 flex items-center text-red-600 hover:text-red-800 transition-colors duration-200"
              >
                <LogOutIcon className="h-5 w-5 mr-2" />
                Sign out
              </button>
            </div>
          </div>

          {/* Main profile content */}
          <div className="flex-1 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-medium text-gray-900">
                Account Information
              </h2>
              {hasChanges() && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Unsaved changes
                </span>
              )}
            </div>
            <ValidatedForm
              onSubmit={handleSubmit}
              validator={createFormValidator}
              initialData={formData}
              onCancel={handleCancel}
              submitText="Save Changes"
              submitingText="Saving..."
              showUnsavedChanges={true}
              confirmBeforeCancel={true}
            >
              {({ formData: currentFormData, updateFormData, validationErrors }) => (
                <>
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    <ValidatedInput
                      label="First name"
                      name="firstName"
                      type="text"
                      value={currentFormData.firstName || formData.firstName}
                      onChange={(e) => {
                        handleInputChange('firstName', e.target.value);
                        updateFormData('firstName', e.target.value);
                      }}
                      validator={new FieldValidator('firstName', currentFormData.firstName || formData.firstName)
                        .required()
                        .maxLength(100)
                        .pattern(/^[a-zA-Z\s]+$/, 'First name can only contain letters')}
                      required
                      placeholder="Enter your first name"
                    />
                    
                    <ValidatedInput
                      label="Last name"
                      name="lastName"
                      type="text"
                      value={currentFormData.lastName || formData.lastName}
                      onChange={(e) => {
                        handleInputChange('lastName', e.target.value);
                        updateFormData('lastName', e.target.value);
                      }}
                      validator={new FieldValidator('lastName', currentFormData.lastName || formData.lastName)
                        .required()
                        .maxLength(100)
                        .pattern(/^[a-zA-Z\s]+$/, 'Last name can only contain letters')}
                      required
                      placeholder="Enter your last name"
                    />
                  </div>
                  
                  <ValidatedInput
                    label="Email"
                    name="email"
                    type="email"
                    value={currentFormData.email || formData.email}
                    onChange={(e) => {
                      handleInputChange('email', e.target.value);
                      updateFormData('email', e.target.value);
                    }}
                    validator={new FieldValidator('email', currentFormData.email || formData.email)
                      .required()
                      .email()}
                    required
                    placeholder="Enter your email address"
                  />
                  
                  <ValidatedInput
                    label="Job title"
                    name="jobTitle"
                    type="text"
                    value={currentFormData.jobTitle || formData.jobTitle}
                    onChange={(e) => {
                      handleInputChange('jobTitle', e.target.value);
                      updateFormData('jobTitle', e.target.value);
                    }}
                    validator={new FieldValidator('jobTitle', currentFormData.jobTitle || formData.jobTitle)
                      .maxLength(200)}
                    placeholder="e.g., Senior Software Engineer"
                  />
                  
                  <ValidatedInput
                    label="Bio"
                    name="bio"
                    type="textarea"
                    rows={4}
                    value={currentFormData.bio || formData.bio}
                    onChange={(e) => {
                      handleInputChange('bio', e.target.value);
                      updateFormData('bio', e.target.value);
                    }}
                    validator={new FieldValidator('bio', currentFormData.bio || formData.bio)
                      .maxLength(1000)}
                    placeholder="Tell us about yourself..."
                    maxLength={1000}
                  />
                </>
              )}
            </ValidatedForm>
            
            {/* Programming Languages Section - Outside of ValidatedForm */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Programming Languages
              </h3>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                {programmingLanguages.map((language) => (
                  <div key={language} className="flex items-center">
                    <input
                      id={`lang-${language}`}
                      type="checkbox"
                      checked={formData.programmingLanguages.includes(
                        language
                      )}
                      onChange={() => handleLanguageToggle(language)}
                      className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    />
                    <label
                      htmlFor={`lang-${language}`}
                      className="ml-3 text-sm font-medium text-gray-700"
                    >
                      {language}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
