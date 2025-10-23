# Enhanced User Service API Integration Guide

## Overview
This guide provides information for integrating the enhanced user service with API endpoints.

## Available Service Methods

### 1. Profile Management

#### `get_user_profile(db: Session, user_id: int) -> Optional[UserProfile]`
Retrieves user profile information.

**Returns:**
```python
UserProfile(
    firstName="John",
    lastName="Doe",
    email="john.doe@example.com",
    jobTitle="Senior Developer",
    bio="Experienced software engineer",
    programmingLanguages=["Python", "JavaScript"],
    profilePictureUrl="/uploads/profile_pictures/123_abc.jpg"
)
```

#### `update_user_profile(db: Session, user_id: int, profile_data: UserProfileUpdate) -> Optional[UserProfile]`
Updates user profile with comprehensive validation.

**Input:**
```python
UserProfileUpdate(
    firstName="John",
    lastName="Doe",
    email="john.doe@example.com",
    jobTitle="Senior Developer",
    bio="Experienced software engineer",
    programmingLanguages=["Python", "JavaScript"]
)
```

**Validations:**
- First/Last name: 1-100 chars, letters/spaces/hyphens/apostrophes/periods only
- Email: Valid format, unique across users
- Job title: Max 200 chars
- Bio: Max 1000 chars
- Programming languages: Max 20 languages, each max 50 chars

**Errors:**
- 404: User not found
- 400: Validation error (empty name, invalid format, duplicate email, etc.)
- 500: Database error

### 2. Preferences Management

#### `get_user_preferences(db: Session, user_id: int) -> Dict[str, Any]`
Retrieves user preferences.

**Returns:**
```python
{
    "notifications": {
        "emailNotifications": {
            "reviewCompleted": True,
            "newPattern": True,
            "securityAlert": True,
            "weeklyDigest": False,
            "marketingEmails": False
        },
        "pushNotifications": {
            "reviewCompleted": True,
            "newPattern": False,
            "securityAlert": True
        },
        "frequency": "immediate"
    },
    "userPreferences": {
        "theme": "dark",
        "language": "en",
        "timezone": "UTC",
        "defaultProgrammingLanguage": "python",
        "aiModel": "gemini-pro",
        "codeEditorTheme": "vs-dark",
        "autoSave": True,
        "showLineNumbers": True
    }
}
```

#### `update_user_preferences(db: Session, user_id: int, preferences: UserPreferences) -> Dict[str, Any]`
Updates user preferences with validation.

**Input:**
```python
UserPreferences(
    theme="dark",
    language="en",
    timezone="UTC",
    defaultProgrammingLanguage="python",
    aiModel="gemini-pro",
    codeEditorTheme="vs-dark",
    autoSave=True,
    showLineNumbers=True
)
```

**Validations:**
- Theme: Must be "light", "dark", or "auto"
- Language: Max 10 chars
- Timezone: Max 50 chars
- AI Model: Must be "gemini-pro", "gemini-1.5-pro", or "gemini-1.5-flash"
- Code Editor Theme: Must be "vs-light", "vs-dark", "hc-black", or "hc-light"

**Errors:**
- 404: User not found
- 400: Invalid theme, AI model, or editor theme
- 500: Database error

### 3. Notification Preferences

#### `update_notification_preferences(db: Session, user_id: int, notifications: NotificationPreferences) -> Dict[str, Any]`
Updates notification preferences.

**Input:**
```python
NotificationPreferences(
    emailNotifications=EmailNotificationSettings(
        reviewCompleted=True,
        newPattern=True,
        securityAlert=True,
        weeklyDigest=False,
        marketingEmails=False
    ),
    pushNotifications=PushNotificationSettings(
        reviewCompleted=True,
        newPattern=False,
        securityAlert=True
    ),
    frequency="immediate"
)
```

**Validations:**
- Frequency: Must be "immediate", "daily", or "weekly"

**Errors:**
- 404: User not found
- 400: Invalid frequency
- 500: Database error

### 4. Profile Picture Management

#### `upload_profile_picture(db: Session, user_id: int, file: UploadFile) -> str`
Uploads profile picture with validation.

**Validations:**
- File type: jpg, jpeg, png, gif, webp
- Content type: Must be image/*
- File size: 1KB - 5MB

**Returns:** Profile picture URL (e.g., "/uploads/profile_pictures/123_abc.jpg")

**Errors:**
- 404: User not found
- 400: Invalid file type, size, or content type
- 500: Upload or database error

#### `delete_profile_picture(db: Session, user_id: int) -> bool`
Deletes user's profile picture.

**Errors:**
- 404: User not found
- 400: No profile picture to delete
- 500: Database error

### 5. Password Management

#### `change_password(db: Session, user_id: int, password_data: PasswordChange) -> bool`
Changes user password with validation.

**Input:**
```python
PasswordChange(
    current_password="OldPassword123",
    new_password="NewPassword123",
    confirm_password="NewPassword123"
)
```

**Validations:**
- Current password must be correct
- New password must be different from current
- Password strength validated by Pydantic schema

**Errors:**
- 404: User not found
- 400: Incorrect current password, same as current, or password not set
- 500: Database error

### 6. Comprehensive Settings

#### `get_user_settings(db: Session, user_id: int) -> Dict[str, Any]`
Gets all user settings (profile + preferences + notifications).

#### `update_user_settings(db: Session, user_id: int, settings: Dict[str, Any]) -> Dict[str, Any]`
Updates comprehensive user settings.

## Example API Endpoint Implementation

### Profile Update Endpoint
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.services.user_service import UserService
from app.schemas.user import UserProfileUpdate, UserProfile

router = APIRouter()
user_service = UserService()

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    try:
        profile = await user_service.update_user_profile(
            db, 
            current_user.id, 
            profile_data
        )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update profile")
```

### Preferences Update Endpoint
```python
@router.put("/preferences")
async def update_preferences(
    preferences: UserPreferences,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    try:
        result = await user_service.update_user_preferences(
            db,
            current_user.id,
            preferences
        )
        return {"success": True, "preferences": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update preferences")
```

### Notification Preferences Update Endpoint
```python
@router.put("/notifications")
async def update_notifications(
    notifications: NotificationPreferences,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences."""
    try:
        result = await user_service.update_notification_preferences(
            db,
            current_user.id,
            notifications
        )
        return {"success": True, "notifications": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update notifications")
```

### Profile Picture Upload Endpoint
```python
from fastapi import File, UploadFile

@router.post("/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload profile picture."""
    try:
        url = await user_service.upload_profile_picture(
            db,
            current_user.id,
            file
        )
        return {"success": True, "profilePictureUrl": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")
```

## Error Handling Best Practices

1. **Always catch HTTPException first** - These are intentional errors with proper status codes
2. **Log unexpected errors** - Use logger for debugging
3. **Return user-friendly messages** - Don't expose internal errors
4. **Use proper status codes**:
   - 400: Validation errors
   - 404: Resource not found
   - 500: Server errors

## Testing Recommendations

1. Test all validation rules
2. Test error handling and rollback
3. Test with invalid data
4. Test with edge cases (empty strings, max lengths, etc.)
5. Test concurrent updates
6. Test file upload limits and types

## Security Considerations

1. **Always authenticate users** - Use `get_current_user` dependency
2. **Validate user ownership** - Ensure users can only update their own data
3. **Sanitize inputs** - Service handles this, but validate at API level too
4. **Rate limiting** - Consider adding rate limits for file uploads
5. **File validation** - Service validates, but consider additional checks

## Performance Tips

1. **Use database indexes** - Ensure email and user_id are indexed
2. **Batch updates** - Consider batching multiple preference updates
3. **Cache preferences** - Consider caching frequently accessed preferences
4. **Async operations** - All service methods are async-ready
5. **File cleanup** - Old profile pictures are automatically deleted

## Migration Notes

If updating from old schema:
1. Ensure `preferences` column exists and is JSON type
2. Migrate old notification preferences to new structure
3. Add email to UserProfileUpdate schema
4. Update frontend to use new notification structure
