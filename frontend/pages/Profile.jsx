import React, { useState, useEffect, useRef } from 'react';
import {
  UserIcon,
  MailIcon,
  KeyIcon,
  LogOutIcon,
  CameraIcon,
  SaveIcon,
  UploadIcon,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useUserProfile } from '../hooks/useUserProfile';
import Toast from '../components/Toast';

export function Profile() {
  const { user, logout } = useAuth();
  const { updateProfile, uploadProfilePicture, isSaving } = useUserProfile();
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

  // Initialize form data when user data is available
  useEffect(() => {
    if (user) {
      setFormData({
        firstName: user.firstName || user.first_name || '',
        lastName: user.lastName || user.last_name || '',
        email: user.email || '',
        jobTitle: user.jobTitle || user.job_title || '',
        bio: user.bio || '',
        programmingLanguages:
          user.programmingLanguages || user.programming_languages || [],
      });

      if (user.profilePictureUrl || user.profile_picture_url) {
        setProfilePicturePreview(
          user.profilePictureUrl || user.profile_picture_url
        );
      }
    }
  }, [user]);

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
      // Validate file type and size
      if (!file.type.startsWith('image/')) {
        showToast('Please select a valid image file', 'error');
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        // 5MB limit
        showToast('Image size must be less than 5MB', 'error');
        return;
      }

      setProfilePicture(file);

      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setProfilePicturePreview(e.target.result);
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
      }
    } catch (error) {
      console.error('Error uploading profile picture:', error);
    } finally {
      setUploadingPicture(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const success = await updateProfile(formData);
    if (!success) {
      // Error handling is done in the hook
      return;
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
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

              {profilePicture && (
                <button
                  onClick={handleProfilePictureUpload}
                  disabled={uploadingPicture}
                  className="mt-2 inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors duration-200"
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
            <h2 className="text-lg font-medium text-gray-900 mb-6">
              Account Information
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label
                    htmlFor="first-name"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    First name
                  </label>
                  <input
                    type="text"
                    id="first-name"
                    value={formData.firstName}
                    onChange={(e) =>
                      handleInputChange('firstName', e.target.value)
                    }
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-white text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-colors duration-200"
                    required
                  />
                </div>
                <div>
                  <label
                    htmlFor="last-name"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Last name
                  </label>
                  <input
                    type="text"
                    id="last-name"
                    value={formData.lastName}
                    onChange={(e) =>
                      handleInputChange('lastName', e.target.value)
                    }
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-white text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-colors duration-200"
                    required
                  />
                </div>
              </div>
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-white text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-colors duration-200"
                  required
                />
              </div>
              <div>
                <label
                  htmlFor="job-title"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Job title
                </label>
                <input
                  type="text"
                  id="job-title"
                  value={formData.jobTitle}
                  onChange={(e) =>
                    handleInputChange('jobTitle', e.target.value)
                  }
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-white text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-colors duration-200"
                  placeholder="e.g., Senior Software Engineer"
                />
              </div>
              <div>
                <label
                  htmlFor="bio"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Bio
                </label>
                <textarea
                  id="bio"
                  rows={4}
                  value={formData.bio}
                  onChange={(e) => handleInputChange('bio', e.target.value)}
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 bg-white text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-colors duration-200"
                  placeholder="Tell us about yourself..."
                />
              </div>
              <div>
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
              <div className="pt-5">
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => window.location.reload()}
                    className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 transition-colors duration-200"
                  >
                    {isSaving ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <SaveIcon className="mr-2 h-4 w-4" />
                        Save
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
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
