import React, { useState, useEffect } from 'react';
import {
     UserIcon,
     MailIcon,
     KeyIcon,
     BellIcon,
     CameraIcon,
     SaveIcon,
     EyeIcon,
     EyeOffIcon,
     CheckIcon,
     XIcon,
     AlertCircleIcon,
     UploadIcon
} from 'lucide-react';
import authService from '../services/authService.js';
import userService from '../services/userService.js';
import Toast from './Toast.jsx';

export default function UserSettings() {
     const [activeTab, setActiveTab] = useState('profile');
     const [user, setUser] = useState(null);
     const [loading, setLoading] = useState(true);
     const [saving, setSaving] = useState(false);
     const [toast, setToast] = useState(null);

     // Profile form state
     const [profileForm, setProfileForm] = useState({
          firstName: '',
          lastName: '',
          email: '',
          jobTitle: '',
          bio: '',
          programmingLanguages: []
     });

     // Password form state
     const [passwordForm, setPasswordForm] = useState({
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
     });

     // Notification preferences state
     const [notificationPrefs, setNotificationPrefs] = useState({
          emailNotifications: {
               reviewCompleted: true,
               newPattern: true,
               securityAlert: true,
               weeklyDigest: false,
               marketingEmails: false
          },
          pushNotifications: {
               reviewCompleted: true,
               newPattern: false,
               securityAlert: true
          },
          frequency: 'immediate' // immediate, daily, weekly
     });

     // User preferences state
     const [userPrefs, setUserPrefs] = useState({
          theme: 'light',
          language: 'en',
          timezone: 'UTC',
          defaultProgrammingLanguage: 'javascript',
          aiModel: 'gemini-pro',
          codeEditorTheme: 'vs-light',
          autoSave: true,
          showLineNumbers: true
     });

     // Profile picture state
     const [profilePicture, setProfilePicture] = useState(null);
     const [profilePicturePreview, setProfilePicturePreview] = useState(null);
     const [uploadingPicture, setUploadingPicture] = useState(false);

     // Password visibility state
     const [showPasswords, setShowPasswords] = useState({
          current: false,
          new: false,
          confirm: false
     });

     // Password validation state
     const [passwordValidation, setPasswordValidation] = useState({
          minLength: false,
          hasUppercase: false,
          hasLowercase: false,
          hasNumber: false,
          hasSpecialChar: false,
          passwordsMatch: false
     });

     useEffect(() => {
          loadUserData();
     }, []);

     useEffect(() => {
          validatePassword();
     }, [passwordForm.newPassword, passwordForm.confirmPassword]);

     const loadUserData = async () => {
          try {
               setLoading(true);
               const currentUser = authService.getCurrentUser();
               if (currentUser) {
                    setUser(currentUser);

                    // Load user profile and preferences
                    const [profileData, preferencesData] = await Promise.all([
                         userService.getUserProfile(currentUser.id),
                         userService.getUserPreferences(currentUser.id)
                    ]);

                    // Set profile form data
                    setProfileForm({
                         firstName: profileData.firstName || '',
                         lastName: profileData.lastName || '',
                         email: profileData.email || currentUser.email,
                         jobTitle: profileData.jobTitle || '',
                         bio: profileData.bio || '',
                         programmingLanguages: profileData.programmingLanguages || []
                    });

                    // Set preferences
                    setNotificationPrefs(preferencesData.notifications || notificationPrefs);
                    setUserPrefs(preferencesData.userPreferences || userPrefs);

                    // Set profile picture
                    if (profileData.profilePictureUrl) {
                         setProfilePicturePreview(profileData.profilePictureUrl);
                    }
               }
          } catch (error) {
               console.error('Error loading user data:', error);
               showToast('Failed to load user data', 'error');
          } finally {
               setLoading(false);
          }
     };

     const validatePassword = () => {
          const password = passwordForm.newPassword;

          setPasswordValidation({
               minLength: password.length >= 8,
               hasUppercase: /[A-Z]/.test(password),
               hasLowercase: /[a-z]/.test(password),
               hasNumber: /\d/.test(password),
               hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
               passwordsMatch: password === passwordForm.confirmPassword && password.length > 0
          });
     };

     const isPasswordValid = () => {
          return Object.values(passwordValidation).every(valid => valid);
     };

     const showToast = (message, type = 'success') => {
          setToast({ message, type });
          setTimeout(() => setToast(null), 5000);
     };

     const handleProfileSubmit = async (e) => {
          e.preventDefault();
          try {
               setSaving(true);
               await userService.updateUserProfile(user.id, profileForm);
               showToast('Profile updated successfully');

               // Update local user data
               const updatedUser = { ...user, ...profileForm };
               setUser(updatedUser);
               authService.setUserData(updatedUser);
          } catch (error) {
               console.error('Error updating profile:', error);
               showToast('Failed to update profile', 'error');
          } finally {
               setSaving(false);
          }
     };

     const handlePasswordSubmit = async (e) => {
          e.preventDefault();

          if (!isPasswordValid()) {
               showToast('Please ensure all password requirements are met', 'error');
               return;
          }

          try {
               setSaving(true);
               await userService.changePassword(user.id, {
                    currentPassword: passwordForm.currentPassword,
                    newPassword: passwordForm.newPassword
               });

               showToast('Password changed successfully');
               setPasswordForm({
                    currentPassword: '',
                    newPassword: '',
                    confirmPassword: ''
               });
          } catch (error) {
               console.error('Error changing password:', error);
               showToast('Failed to change password', 'error');
          } finally {
               setSaving(false);
          }
     };

     const handleNotificationSubmit = async (e) => {
          e.preventDefault();
          try {
               setSaving(true);
               await userService.updateNotificationPreferences(user.id, notificationPrefs);
               showToast('Notification preferences updated successfully');
          } catch (error) {
               console.error('Error updating notification preferences:', error);
               showToast('Failed to update notification preferences', 'error');
          } finally {
               setSaving(false);
          }
     };

     const handlePreferencesSubmit = async (e) => {
          e.preventDefault();
          try {
               setSaving(true);
               await userService.updateUserPreferences(user.id, userPrefs);
               showToast('Preferences updated successfully');
          } catch (error) {
               console.error('Error updating preferences:', error);
               showToast('Failed to update preferences', 'error');
          } finally {
               setSaving(false);
          }
     };

     const handleProfilePictureChange = (e) => {
          const file = e.target.files[0];
          if (file) {
               // Validate file type and size
               if (!file.type.startsWith('image/')) {
                    showToast('Please select a valid image file', 'error');
                    return;
               }

               if (file.size > 5 * 1024 * 1024) { // 5MB limit
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
               const uploadedUrl = await userService.uploadProfilePicture(user.id, profilePicture);
               showToast('Profile picture updated successfully');
               setProfilePicture(null);
               setProfilePicturePreview(uploadedUrl);
          } catch (error) {
               console.error('Error uploading profile picture:', error);
               showToast('Failed to upload profile picture', 'error');
          } finally {
               setUploadingPicture(false);
          }
     };

     const togglePasswordVisibility = (field) => {
          setShowPasswords(prev => ({
               ...prev,
               [field]: !prev[field]
          }));
     };

     if (loading) {
          return (
               <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
               </div>
          );
     }

     return (
          <div className="w-full max-w-6xl mx-auto">
               <h1 className="text-2xl font-bold mb-6">User Settings</h1>

               <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
                    <div className="md:flex">
                         {/* Settings Navigation */}
                         <div className="md:w-64 bg-gray-50 md:border-r border-gray-200">
                              <nav className="flex flex-col md:h-full py-4">
                                   <button
                                        onClick={() => setActiveTab('profile')}
                                        className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'profile'
                                             ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700'
                                             : 'text-gray-600 hover:bg-gray-100'
                                             }`}
                                   >
                                        <UserIcon className="mr-3 h-5 w-5" />
                                        Profile
                                   </button>

                                   <button
                                        onClick={() => setActiveTab('security')}
                                        className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'security'
                                             ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700'
                                             : 'text-gray-600 hover:bg-gray-100'
                                             }`}
                                   >
                                        <KeyIcon className="mr-3 h-5 w-5" />
                                        Security
                                   </button>

                                   <button
                                        onClick={() => setActiveTab('notifications')}
                                        className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'notifications'
                                             ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700'
                                             : 'text-gray-600 hover:bg-gray-100'
                                             }`}
                                   >
                                        <BellIcon className="mr-3 h-5 w-5" />
                                        Notifications
                                   </button>

                                   <button
                                        onClick={() => setActiveTab('preferences')}
                                        className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'preferences'
                                             ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700'
                                             : 'text-gray-600 hover:bg-gray-100'
                                             }`}
                                   >
                                        <MailIcon className="mr-3 h-5 w-5" />
                                        Preferences
                                   </button>
                              </nav>
                         </div>

                         {/* Settings Content */}
                         <div className="flex-1 p-6">
                              {activeTab === 'profile' && (
                                   <ProfileTab
                                        profileForm={profileForm}
                                        setProfileForm={setProfileForm}
                                        profilePicturePreview={profilePicturePreview}
                                        profilePicture={profilePicture}
                                        uploadingPicture={uploadingPicture}
                                        saving={saving}
                                        onSubmit={handleProfileSubmit}
                                        onPictureChange={handleProfilePictureChange}
                                        onPictureUpload={handleProfilePictureUpload}
                                   />
                              )}

                              {activeTab === 'security' && (
                                   <SecurityTab
                                        passwordForm={passwordForm}
                                        setPasswordForm={setPasswordForm}
                                        showPasswords={showPasswords}
                                        passwordValidation={passwordValidation}
                                        saving={saving}
                                        onSubmit={handlePasswordSubmit}
                                        onToggleVisibility={togglePasswordVisibility}
                                   />
                              )}

                              {activeTab === 'notifications' && (
                                   <NotificationsTab
                                        notificationPrefs={notificationPrefs}
                                        setNotificationPrefs={setNotificationPrefs}
                                        saving={saving}
                                        onSubmit={handleNotificationSubmit}
                                   />
                              )}

                              {activeTab === 'preferences' && (
                                   <PreferencesTab
                                        userPrefs={userPrefs}
                                        setUserPrefs={setUserPrefs}
                                        saving={saving}
                                        onSubmit={handlePreferencesSubmit}
                                   />
                              )}
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

// Profile Tab Component
function ProfileTab({
     profileForm,
     setProfileForm,
     profilePicturePreview,
     profilePicture,
     uploadingPicture,
     saving,
     onSubmit,
     onPictureChange,
     onPictureUpload
}) {
     const programmingLanguages = [
          'JavaScript', 'TypeScript', 'Python', 'Java', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Swift'
     ];

     const handleLanguageToggle = (language) => {
          setProfileForm(prev => ({
               ...prev,
               programmingLanguages: prev.programmingLanguages.includes(language)
                    ? prev.programmingLanguages.filter(lang => lang !== language)
                    : [...prev.programmingLanguages, language]
          }));
     };

     return (
          <div>
               <h2 className="text-lg font-medium text-gray-900 mb-4">Profile Information</h2>

               <form onSubmit={onSubmit} className="space-y-6">
                    {/* Profile Picture Section */}
                    <div className="flex items-center space-x-6">
                         <div className="relative">
                              <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
                                   {profilePicturePreview ? (
                                        <img
                                             src={profilePicturePreview}
                                             alt="Profile"
                                             className="w-full h-full object-cover"
                                        />
                                   ) : (
                                        <UserIcon className="h-12 w-12 text-gray-400" />
                                   )}
                              </div>
                              <label
                                   htmlFor="profile-picture"
                                   className="absolute bottom-0 right-0 bg-indigo-600 p-2 rounded-full text-white cursor-pointer hover:bg-indigo-700"
                              >
                                   <CameraIcon className="h-4 w-4" />
                              </label>
                              <input
                                   id="profile-picture"
                                   type="file"
                                   accept="image/*"
                                   onChange={onPictureChange}
                                   className="hidden"
                              />
                         </div>

                         <div className="flex-1">
                              <h3 className="text-sm font-medium text-gray-900">Profile Picture</h3>
                              <p className="text-sm text-gray-500">
                                   Upload a new profile picture. Max size: 5MB
                              </p>
                              {profilePicture && (
                                   <button
                                        type="button"
                                        onClick={onPictureUpload}
                                        disabled={uploadingPicture}
                                        className="mt-2 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                                   >
                                        {uploadingPicture ? (
                                             <>
                                                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                  Uploading...
                                             </>
                                        ) : (
                                             <>
                                                  <UploadIcon className="mr-2 h-4 w-4" />
                                                  Upload Picture
                                             </>
                                        )}
                                   </button>
                              )}
                         </div>
                    </div>

                    {/* Basic Information */}
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                         <div>
                              <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                                   First Name
                              </label>
                              <input
                                   type="text"
                                   id="firstName"
                                   value={profileForm.firstName}
                                   onChange={(e) => setProfileForm(prev => ({ ...prev, firstName: e.target.value }))}
                                   className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                   required
                              />
                         </div>

                         <div>
                              <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                                   Last Name
                              </label>
                              <input
                                   type="text"
                                   id="lastName"
                                   value={profileForm.lastName}
                                   onChange={(e) => setProfileForm(prev => ({ ...prev, lastName: e.target.value }))}
                                   className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                   required
                              />
                         </div>
                    </div>

                    <div>
                         <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                              Email Address
                         </label>
                         <input
                              type="email"
                              id="email"
                              value={profileForm.email}
                              onChange={(e) => setProfileForm(prev => ({ ...prev, email: e.target.value }))}
                              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                              required
                         />
                    </div>

                    <div>
                         <label htmlFor="jobTitle" className="block text-sm font-medium text-gray-700 mb-1">
                              Job Title
                         </label>
                         <input
                              type="text"
                              id="jobTitle"
                              value={profileForm.jobTitle}
                              onChange={(e) => setProfileForm(prev => ({ ...prev, jobTitle: e.target.value }))}
                              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                              placeholder="e.g., Senior Software Engineer"
                         />
                    </div>

                    <div>
                         <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-1">
                              Bio
                         </label>
                         <textarea
                              id="bio"
                              rows={4}
                              value={profileForm.bio}
                              onChange={(e) => setProfileForm(prev => ({ ...prev, bio: e.target.value }))}
                              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                              placeholder="Tell us about yourself..."
                         />
                    </div>

                    {/* Programming Languages */}
                    <div>
                         <label className="block text-sm font-medium text-gray-700 mb-3">
                              Programming Languages
                         </label>
                         <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                              {programmingLanguages.map((language) => (
                                   <div key={language} className="flex items-center">
                                        <input
                                             id={`lang-${language}`}
                                             type="checkbox"
                                             checked={profileForm.programmingLanguages.includes(language)}
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

                    {/* Submit Button */}
                    <div className="pt-5">
                         <div className="flex justify-end">
                              <button
                                   type="submit"
                                   disabled={saving}
                                   className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                              >
                                   {saving ? (
                                        <>
                                             <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                             Saving...
                                        </>
                                   ) : (
                                        <>
                                             <SaveIcon className="mr-2 h-4 w-4" />
                                             Save Profile
                                        </>
                                   )}
                              </button>
                         </div>
                    </div>
               </form>
          </div>
     );
}

// Security Tab Component
function SecurityTab({
     passwordForm,
     setPasswordForm,
     showPasswords,
     passwordValidation,
     saving,
     onSubmit,
     onToggleVisibility
}) {
     const ValidationIcon = ({ isValid }) => (
          isValid ? (
               <CheckIcon className="h-4 w-4 text-green-500" />
          ) : (
               <XIcon className="h-4 w-4 text-red-500" />
          )
     );

     return (
          <div>
               <h2 className="text-lg font-medium text-gray-900 mb-4">Security Settings</h2>

               <form onSubmit={onSubmit} className="space-y-6">
                    {/* Current Password */}
                    <div>
                         <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-1">
                              Current Password
                         </label>
                         <div className="relative">
                              <input
                                   type={showPasswords.current ? 'text' : 'password'}
                                   id="currentPassword"
                                   value={passwordForm.currentPassword}
                                   onChange={(e) => setPasswordForm(prev => ({ ...prev, currentPassword: e.target.value }))}
                                   className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                   required
                              />
                              <button
                                   type="button"
                                   onClick={() => onToggleVisibility('current')}
                                   className="absolute inset-y-0 right-0 pr-3 flex items-center"
                              >
                                   {showPasswords.current ? (
                                        <EyeOffIcon className="h-5 w-5 text-gray-400" />
                                   ) : (
                                        <EyeIcon className="h-5 w-5 text-gray-400" />
                                   )}
                              </button>
                         </div>
                    </div>

                    {/* New Password */}
                    <div>
                         <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">
                              New Password
                         </label>
                         <div className="relative">
                              <input
                                   type={showPasswords.new ? 'text' : 'password'}
                                   id="newPassword"
                                   value={passwordForm.newPassword}
                                   onChange={(e) => setPasswordForm(prev => ({ ...prev, newPassword: e.target.value }))}
                                   className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                   required
                              />
                              <button
                                   type="button"
                                   onClick={() => onToggleVisibility('new')}
                                   className="absolute inset-y-0 right-0 pr-3 flex items-center"
                              >
                                   {showPasswords.new ? (
                                        <EyeOffIcon className="h-5 w-5 text-gray-400" />
                                   ) : (
                                        <EyeIcon className="h-5 w-5 text-gray-400" />
                                   )}
                              </button>
                         </div>
                    </div>

                    {/* Confirm Password */}
                    <div>
                         <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                              Confirm New Password
                         </label>
                         <div className="relative">
                              <input
                                   type={showPasswords.confirm ? 'text' : 'password'}
                                   id="confirmPassword"
                                   value={passwordForm.confirmPassword}
                                   onChange={(e) => setPasswordForm(prev => ({ ...prev, confirmPassword: e.target.value }))}
                                   className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pr-10 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                                   required
                              />
                              <button
                                   type="button"
                                   onClick={() => onToggleVisibility('confirm')}
                                   className="absolute inset-y-0 right-0 pr-3 flex items-center"
                              >
                                   {showPasswords.confirm ? (
                                        <EyeOffIcon className="h-5 w-5 text-gray-400" />
                                   ) : (
                                        <EyeIcon className="h-5 w-5 text-gray-400" />
                                   )}
                              </button>
                         </div>
                    </div>

                    {/* Password Requirements */}
                    {passwordForm.newPassword && (
                         <div className="bg-gray-50 p-4 rounded-md">
                              <h4 className="text-sm font-medium text-gray-900 mb-3">Password Requirements</h4>
                              <div className="space-y-2">
                                   <div className="flex items-center">
                                        <ValidationIcon isValid={passwordValidation.minLength} />
                                        <span className={`ml-2 text-sm ${passwordValidation.minLength ? 'text-green-700' : 'text-red-700'}`}>
                                             At least 8 characters
                                        </span>
                                   </div>
                                   <div className="flex items-center">
                                        <ValidationIcon isValid={passwordValidation.hasUppercase} />
                                        <span className={`ml-2 text-sm ${passwordValidation.hasUppercase ? 'text-green-700' : 'text-red-700'}`}>
                                             At least one uppercase letter
                                        </span>
                                   </div>
                                   <div className="flex items-center">
                                        <ValidationIcon isValid={passwordValidation.hasLowercase} />
                                        <span className={`ml-2 text-sm ${passwordValidation.hasLowercase ? 'text-green-700' : 'text-red-700'}`}>
                                             At least one lowercase letter
                                        </span>
                                   </div>
                                   <div className="flex items-center">
                                        <ValidationIcon isValid={passwordValidation.hasNumber} />
                                        <span className={`ml-2 text-sm ${passwordValidation.hasNumber ? 'text-green-700' : 'text-red-700'}`}>
                                             At least one number
                                        </span>
                                   </div>
                                   <div className="flex items-center">
                                        <ValidationIcon isValid={passwordValidation.hasSpecialChar} />
                                        <span className={`ml-2 text-sm ${passwordValidation.hasSpecialChar ? 'text-green-700' : 'text-red-700'}`}>
                                             At least one special character
                                        </span>
                                   </div>
                                   <div className="flex items-center">
                                        <ValidationIcon isValid={passwordValidation.passwordsMatch} />
                                        <span className={`ml-2 text-sm ${passwordValidation.passwordsMatch ? 'text-green-700' : 'text-red-700'}`}>
                                             Passwords match
                                        </span>
                                   </div>
                              </div>
                         </div>
                    )}

                    {/* Security Tips */}
                    <div className="bg-blue-50 p-4 rounded-md">
                         <div className="flex">
                              <AlertCircleIcon className="h-5 w-5 text-blue-400" />
                              <div className="ml-3">
                                   <h4 className="text-sm font-medium text-blue-800">Security Tips</h4>
                                   <div className="mt-2 text-sm text-blue-700">
                                        <ul className="list-disc list-inside space-y-1">
                                             <li>Use a unique password that you don't use elsewhere</li>
                                             <li>Consider using a password manager</li>
                                             <li>Enable two-factor authentication for additional security</li>
                                        </ul>
                                   </div>
                              </div>
                         </div>
                    </div>

                    {/* Submit Button */}
                    <div className="pt-5">
                         <div className="flex justify-end">
                              <button
                                   type="submit"
                                   disabled={saving || !Object.values(passwordValidation).every(valid => valid)}
                                   className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                              >
                                   {saving ? (
                                        <>
                                             <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                             Changing Password...
                                        </>
                                   ) : (
                                        <>
                                             <KeyIcon className="mr-2 h-4 w-4" />
                                             Change Password
                                        </>
                                   )}
                              </button>
                         </div>
                    </div>
               </form>
          </div>
     );
}

// Notifications Tab Component
function NotificationsTab({
     notificationPrefs,
     setNotificationPrefs,
     saving,
     onSubmit
}) {
     const handleEmailNotificationChange = (key, value) => {
          setNotificationPrefs(prev => ({
               ...prev,
               emailNotifications: {
                    ...prev.emailNotifications,
                    [key]: value
               }
          }));
     };

     const handlePushNotificationChange = (key, value) => {
          setNotificationPrefs(prev => ({
               ...prev,
               pushNotifications: {
                    ...prev.pushNotifications,
                    [key]: value
               }
          }));
     };

     const handleFrequencyChange = (frequency) => {
          setNotificationPrefs(prev => ({
               ...prev,
               frequency
          }));
     };

     return (
          <div>
               <h2 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h2>
               <p className="text-gray-500 mb-6">
                    Configure how and when you receive notifications about code reviews, patterns, and system updates.
               </p>

               <form onSubmit={onSubmit} className="space-y-8">
                    {/* Email Notifications */}
                    <div>
                         <h3 className="text-sm font-medium text-gray-900 mb-4">Email Notifications</h3>
                         <div className="space-y-4">
                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="email-review-completed"
                                             type="checkbox"
                                             checked={notificationPrefs.emailNotifications.reviewCompleted}
                                             onChange={(e) => handleEmailNotificationChange('reviewCompleted', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="email-review-completed" className="font-medium text-gray-700">
                                             Review completed
                                        </label>
                                        <p className="text-gray-500">Get notified when a code review is completed</p>
                                   </div>
                              </div>

                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="email-new-pattern"
                                             type="checkbox"
                                             checked={notificationPrefs.emailNotifications.newPattern}
                                             onChange={(e) => handleEmailNotificationChange('newPattern', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="email-new-pattern" className="font-medium text-gray-700">
                                             New pattern detected
                                        </label>
                                        <p className="text-gray-500">Get notified when the AI identifies a new code pattern</p>
                                   </div>
                              </div>

                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="email-security-alert"
                                             type="checkbox"
                                             checked={notificationPrefs.emailNotifications.securityAlert}
                                             onChange={(e) => handleEmailNotificationChange('securityAlert', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="email-security-alert" className="font-medium text-gray-700">
                                             Security alerts
                                        </label>
                                        <p className="text-gray-500">Get notified about critical security issues</p>
                                   </div>
                              </div>

                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="email-weekly-digest"
                                             type="checkbox"
                                             checked={notificationPrefs.emailNotifications.weeklyDigest}
                                             onChange={(e) => handleEmailNotificationChange('weeklyDigest', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="email-weekly-digest" className="font-medium text-gray-700">
                                             Weekly digest
                                        </label>
                                        <p className="text-gray-500">Receive a weekly summary of your activity and insights</p>
                                   </div>
                              </div>

                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="email-marketing"
                                             type="checkbox"
                                             checked={notificationPrefs.emailNotifications.marketingEmails}
                                             onChange={(e) => handleEmailNotificationChange('marketingEmails', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="email-marketing" className="font-medium text-gray-700">
                                             Marketing emails
                                        </label>
                                        <p className="text-gray-500">Receive updates about new features and product announcements</p>
                                   </div>
                              </div>
                         </div>
                    </div>

                    {/* Push Notifications */}
                    <div>
                         <h3 className="text-sm font-medium text-gray-900 mb-4">Push Notifications</h3>
                         <div className="space-y-4">
                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="push-review-completed"
                                             type="checkbox"
                                             checked={notificationPrefs.pushNotifications.reviewCompleted}
                                             onChange={(e) => handlePushNotificationChange('reviewCompleted', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="push-review-completed" className="font-medium text-gray-700">
                                             Review completed
                                        </label>
                                        <p className="text-gray-500">Get push notifications when reviews are completed</p>
                                   </div>
                              </div>

                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="push-new-pattern"
                                             type="checkbox"
                                             checked={notificationPrefs.pushNotifications.newPattern}
                                             onChange={(e) => handlePushNotificationChange('newPattern', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="push-new-pattern" className="font-medium text-gray-700">
                                             New pattern detected
                                        </label>
                                        <p className="text-gray-500">Get push notifications for new patterns</p>
                                   </div>
                              </div>

                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="push-security-alert"
                                             type="checkbox"
                                             checked={notificationPrefs.pushNotifications.securityAlert}
                                             onChange={(e) => handlePushNotificationChange('securityAlert', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="push-security-alert" className="font-medium text-gray-700">
                                             Security alerts
                                        </label>
                                        <p className="text-gray-500">Get immediate push notifications for security issues</p>
                                   </div>
                              </div>
                         </div>
                    </div>

                    {/* Notification Frequency */}
                    <div>
                         <h3 className="text-sm font-medium text-gray-900 mb-4">Notification Frequency</h3>
                         <div className="space-y-4">
                              <div className="flex items-center">
                                   <input
                                        id="frequency-immediate"
                                        name="frequency"
                                        type="radio"
                                        checked={notificationPrefs.frequency === 'immediate'}
                                        onChange={() => handleFrequencyChange('immediate')}
                                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                                   />
                                   <label htmlFor="frequency-immediate" className="ml-3 block text-sm font-medium text-gray-700">
                                        Immediate
                                   </label>
                              </div>
                              <div className="flex items-center">
                                   <input
                                        id="frequency-daily"
                                        name="frequency"
                                        type="radio"
                                        checked={notificationPrefs.frequency === 'daily'}
                                        onChange={() => handleFrequencyChange('daily')}
                                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                                   />
                                   <label htmlFor="frequency-daily" className="ml-3 block text-sm font-medium text-gray-700">
                                        Daily digest
                                   </label>
                              </div>
                              <div className="flex items-center">
                                   <input
                                        id="frequency-weekly"
                                        name="frequency"
                                        type="radio"
                                        checked={notificationPrefs.frequency === 'weekly'}
                                        onChange={() => handleFrequencyChange('weekly')}
                                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                                   />
                                   <label htmlFor="frequency-weekly" className="ml-3 block text-sm font-medium text-gray-700">
                                        Weekly digest
                                   </label>
                              </div>
                         </div>
                    </div>

                    {/* Submit Button */}
                    <div className="pt-5">
                         <div className="flex justify-end">
                              <button
                                   type="submit"
                                   disabled={saving}
                                   className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                              >
                                   {saving ? (
                                        <>
                                             <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                             Saving...
                                        </>
                                   ) : (
                                        <>
                                             <SaveIcon className="mr-2 h-4 w-4" />
                                             Save Preferences
                                        </>
                                   )}
                              </button>
                         </div>
                    </div>
               </form>
          </div>
     );
}

// Preferences Tab Component
function PreferencesTab({
     userPrefs,
     setUserPrefs,
     saving,
     onSubmit
}) {
     const handlePrefChange = (key, value) => {
          setUserPrefs(prev => ({
               ...prev,
               [key]: value
          }));
     };

     const themes = [
          { value: 'light', label: 'Light' },
          { value: 'dark', label: 'Dark' },
          { value: 'system', label: 'System Default' }
     ];

     const languages = [
          { value: 'en', label: 'English' },
          { value: 'es', label: 'Spanish' },
          { value: 'fr', label: 'French' },
          { value: 'de', label: 'German' },
          { value: 'ja', label: 'Japanese' },
          { value: 'zh', label: 'Chinese' }
     ];

     const timezones = [
          { value: 'UTC', label: 'UTC' },
          { value: 'America/New_York', label: 'Eastern Time' },
          { value: 'America/Chicago', label: 'Central Time' },
          { value: 'America/Denver', label: 'Mountain Time' },
          { value: 'America/Los_Angeles', label: 'Pacific Time' },
          { value: 'Europe/London', label: 'London' },
          { value: 'Europe/Paris', label: 'Paris' },
          { value: 'Asia/Tokyo', label: 'Tokyo' },
          { value: 'Asia/Shanghai', label: 'Shanghai' }
     ];

     const programmingLanguages = [
          { value: 'javascript', label: 'JavaScript' },
          { value: 'typescript', label: 'TypeScript' },
          { value: 'python', label: 'Python' },
          { value: 'java', label: 'Java' },
          { value: 'csharp', label: 'C#' },
          { value: 'go', label: 'Go' },
          { value: 'rust', label: 'Rust' },
          { value: 'php', label: 'PHP' }
     ];

     const aiModels = [
          { value: 'gemini-pro', label: 'Gemini Pro (Recommended)' },
          { value: 'gemini-standard', label: 'Gemini Standard' },
          { value: 'gpt-4', label: 'GPT-4' },
          { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
     ];

     const editorThemes = [
          { value: 'vs-light', label: 'Light' },
          { value: 'vs-dark', label: 'Dark' },
          { value: 'hc-black', label: 'High Contrast' }
     ];

     return (
          <div>
               <h2 className="text-lg font-medium text-gray-900 mb-4">User Preferences</h2>
               <p className="text-gray-500 mb-6">
                    Customize your experience with personalized settings and preferences.
               </p>

               <form onSubmit={onSubmit} className="space-y-8">
                    {/* Appearance */}
                    <div>
                         <h3 className="text-sm font-medium text-gray-900 mb-4">Appearance</h3>
                         <div className="space-y-4">
                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
                                   <div className="space-y-2">
                                        {themes.map((theme) => (
                                             <div key={theme.value} className="flex items-center">
                                                  <input
                                                       id={`theme-${theme.value}`}
                                                       name="theme"
                                                       type="radio"
                                                       checked={userPrefs.theme === theme.value}
                                                       onChange={() => handlePrefChange('theme', theme.value)}
                                                       className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                                                  />
                                                  <label htmlFor={`theme-${theme.value}`} className="ml-3 block text-sm font-medium text-gray-700">
                                                       {theme.label}
                                                  </label>
                                             </div>
                                        ))}
                                   </div>
                              </div>

                              <div>
                                   <label htmlFor="editor-theme" className="block text-sm font-medium text-gray-700 mb-1">
                                        Code Editor Theme
                                   </label>
                                   <select
                                        id="editor-theme"
                                        value={userPrefs.codeEditorTheme}
                                        onChange={(e) => handlePrefChange('codeEditorTheme', e.target.value)}
                                        className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                                   >
                                        {editorThemes.map((theme) => (
                                             <option key={theme.value} value={theme.value}>
                                                  {theme.label}
                                             </option>
                                        ))}
                                   </select>
                              </div>
                         </div>
                    </div>

                    {/* Localization */}
                    <div>
                         <h3 className="text-sm font-medium text-gray-900 mb-4">Localization</h3>
                         <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                              <div>
                                   <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
                                        Language
                                   </label>
                                   <select
                                        id="language"
                                        value={userPrefs.language}
                                        onChange={(e) => handlePrefChange('language', e.target.value)}
                                        className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                                   >
                                        {languages.map((lang) => (
                                             <option key={lang.value} value={lang.value}>
                                                  {lang.label}
                                             </option>
                                        ))}
                                   </select>
                              </div>

                              <div>
                                   <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-1">
                                        Timezone
                                   </label>
                                   <select
                                        id="timezone"
                                        value={userPrefs.timezone}
                                        onChange={(e) => handlePrefChange('timezone', e.target.value)}
                                        className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                                   >
                                        {timezones.map((tz) => (
                                             <option key={tz.value} value={tz.value}>
                                                  {tz.label}
                                             </option>
                                        ))}
                                   </select>
                              </div>
                         </div>
                    </div>

                    {/* Development Preferences */}
                    <div>
                         <h3 className="text-sm font-medium text-gray-900 mb-4">Development Preferences</h3>
                         <div className="space-y-4">
                              <div>
                                   <label htmlFor="default-language" className="block text-sm font-medium text-gray-700 mb-1">
                                        Default Programming Language
                                   </label>
                                   <select
                                        id="default-language"
                                        value={userPrefs.defaultProgrammingLanguage}
                                        onChange={(e) => handlePrefChange('defaultProgrammingLanguage', e.target.value)}
                                        className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                                   >
                                        {programmingLanguages.map((lang) => (
                                             <option key={lang.value} value={lang.value}>
                                                  {lang.label}
                                             </option>
                                        ))}
                                   </select>
                              </div>

                              <div>
                                   <label htmlFor="ai-model" className="block text-sm font-medium text-gray-700 mb-1">
                                        AI Model
                                   </label>
                                   <select
                                        id="ai-model"
                                        value={userPrefs.aiModel}
                                        onChange={(e) => handlePrefChange('aiModel', e.target.value)}
                                        className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                                   >
                                        {aiModels.map((model) => (
                                             <option key={model.value} value={model.value}>
                                                  {model.label}
                                             </option>
                                        ))}
                                   </select>
                              </div>
                         </div>
                    </div>

                    {/* Editor Preferences */}
                    <div>
                         <h3 className="text-sm font-medium text-gray-900 mb-4">Editor Preferences</h3>
                         <div className="space-y-4">
                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="auto-save"
                                             type="checkbox"
                                             checked={userPrefs.autoSave}
                                             onChange={(e) => handlePrefChange('autoSave', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="auto-save" className="font-medium text-gray-700">
                                             Auto-save
                                        </label>
                                        <p className="text-gray-500">Automatically save your work as you type</p>
                                   </div>
                              </div>

                              <div className="flex items-start">
                                   <div className="flex items-center h-5">
                                        <input
                                             id="show-line-numbers"
                                             type="checkbox"
                                             checked={userPrefs.showLineNumbers}
                                             onChange={(e) => handlePrefChange('showLineNumbers', e.target.checked)}
                                             className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                                        />
                                   </div>
                                   <div className="ml-3 text-sm">
                                        <label htmlFor="show-line-numbers" className="font-medium text-gray-700">
                                             Show line numbers
                                        </label>
                                        <p className="text-gray-500">Display line numbers in the code editor</p>
                                   </div>
                              </div>
                         </div>
                    </div>

                    {/* Submit Button */}
                    <div className="pt-5">
                         <div className="flex justify-end">
                              <button
                                   type="submit"
                                   disabled={saving}
                                   className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                              >
                                   {saving ? (
                                        <>
                                             <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                             Saving...
                                        </>
                                   ) : (
                                        <>
                                             <SaveIcon className="mr-2 h-4 w-4" />
                                             Save Preferences
                                        </>
                                   )}
                              </button>
                         </div>
                    </div>
               </form>
          </div>
     );
}