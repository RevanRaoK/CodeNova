# API Key Management Documentation

## Overview

The API Key Management feature allows users to provide their own Gemini API keys for code analysis. When a user provides their own API key, the system will use it instead of the default API key for all their analysis requests.

## Features

- **Secure Storage**: API keys are encrypted using Fernet (symmetric encryption) before being stored in the database
- **User-Specific Keys**: Each user can have their own API key
- **Automatic Usage**: When available, user's API key is automatically used for their analysis requests
- **Key Management**: Users can view, update, and delete their API keys

## Architecture

### Components

1. **Encryption Service** (`app/core/encryption.py`)
   - Handles encryption/decryption of API keys
   - Uses PBKDF2 key derivation with SHA256
   - Provides key masking for display purposes

2. **User Service** (`app/services/user_service.py`)
   - `get_api_key_status()`: Check if user has an API key
   - `save_api_key()`: Save encrypted API key
   - `delete_api_key()`: Remove API key
   - `get_decrypted_api_key()`: Retrieve decrypted key for use

3. **AI Service** (`app/services/ai_service.py`)
   - `get_ai_service_for_user()`: Returns AI service instance with user's key or default

4. **API Endpoints** (`app/api/v1/endpoints/users.py`)
   - `GET /api/v1/users/api-key`: Get API key status
   - `PUT /api/v1/users/api-key`: Save API key
   - `DELETE /api/v1/users/api-key`: Delete API key

### Database Schema

```sql
ALTER TABLE users ADD COLUMN gemini_api_key VARCHAR(512);
```

The `gemini_api_key` column stores the encrypted API key (up to 512 characters).

## API Endpoints

### Get API Key Status

**Endpoint**: `GET /api/v1/users/api-key`

**Authentication**: Required (Bearer token)

**Response**:
```json
{
  "hasKey": true,
  "keyPreview": "****6789"
}
```

### Save API Key

**Endpoint**: `PUT /api/v1/users/api-key`

**Authentication**: Required (Bearer token)

**Request Body**:
```json
{
  "apiKey": "AIzaSyDummyTestKey123456789"
}
```

**Response**:
```json
{
  "success": true,
  "message": "API key saved successfully",
  "keyPreview": "****6789"
}
```

**Validation**:
- API key must be at least 10 characters
- Warning logged if key doesn't start with "AIza" (Gemini key prefix)

### Delete API Key

**Endpoint**: `DELETE /api/v1/users/api-key`

**Authentication**: Required (Bearer token)

**Response**:
```json
{
  "success": true,
  "message": "API key deleted successfully"
}
```

## Security Considerations

### Encryption

- API keys are encrypted using Fernet (symmetric encryption)
- Encryption key is derived from the application's SECRET_KEY using PBKDF2
- 100,000 iterations for key derivation
- SHA256 hashing algorithm

### Key Derivation

```python
kdf = PBKDF2(
    algorithm=hashes.SHA256(),
    length=32,
    salt=b'code_review_platform_salt_v1',
    iterations=100000,
    backend=default_backend()
)
```

### Best Practices

1. **Never log decrypted keys**: Keys are only decrypted when needed for API calls
2. **Masked display**: Keys are masked when shown to users (e.g., "****6789")
3. **Secure transmission**: API endpoints require authentication
4. **Error handling**: Decryption errors are logged but don't expose key data

## Usage Flow

### User Provides API Key

1. User navigates to Settings → API Access tab
2. User enters their Gemini API key
3. Frontend calls `PUT /api/v1/users/api-key`
4. Backend validates and encrypts the key
5. Encrypted key is stored in database
6. User sees masked preview of their key

### Analysis with User's Key

1. User submits code for analysis
2. Analysis endpoint calls `get_ai_service_for_user(user_id, db)`
3. Function checks if user has a custom API key
4. If yes, decrypts key and creates AI service instance with it
5. If no, uses default API key
6. Analysis proceeds with appropriate key

### User Deletes API Key

1. User clicks "Delete API Key" in settings
2. Frontend calls `DELETE /api/v1/users/api-key`
3. Backend removes key from database
4. Future analyses use default API key

## Error Handling

### Encryption Errors

```python
try:
    encrypted_key = encrypt_api_key(api_key)
except ValueError as e:
    raise HTTPException(status_code=500, detail="Failed to encrypt API key")
```

### Decryption Errors

```python
try:
    decrypted_key = decrypt_api_key(encrypted_key)
except Exception as e:
    logger.error(f"Failed to decrypt API key for user {user_id}: {e}")
    return None  # Fall back to default key
```

### Database Errors

```python
try:
    db.commit()
except IntegrityError as e:
    db.rollback()
    raise HTTPException(status_code=500, detail="Failed to save API key")
```

## Testing

Run the test script to verify functionality:

```bash
python backend/test_api_key_management.py
```

The test script verifies:
1. Encryption/Decryption
2. Key masking
3. Saving API keys
4. Retrieving API key status
5. Getting decrypted keys
6. AI service integration
7. Deleting API keys
8. Verification after deletion

## Frontend Integration

### Settings Page (API Access Tab)

```typescript
// Get API key status
const response = await fetch('/api/v1/users/api-key', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { hasKey, keyPreview } = await response.json();

// Save API key
const saveResponse = await fetch('/api/v1/users/api-key', {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ apiKey: userInputKey })
});

// Delete API key
const deleteResponse = await fetch('/api/v1/users/api-key', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

## Requirements Covered

This implementation covers the following requirements from the spec:

- **4.8**: User can configure their own Gemini API key in API Access tab
- **4.9**: System uses user's API key for their analysis requests
- **6.6**: API returns user's API key securely (masked)
- **6.7**: API validates and stores API key encrypted
- **6.8**: Analysis uses user-provided API key when available

## Future Enhancements

1. **Key Validation**: Test API key validity before saving
2. **Multiple Keys**: Support for multiple API providers (OpenAI, Claude, etc.)
3. **Usage Tracking**: Track API usage per user's key
4. **Key Rotation**: Automatic key rotation reminders
5. **Key Expiration**: Support for time-limited keys
