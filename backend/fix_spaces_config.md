# Fix Digital Ocean Spaces Configuration

## Current Issue

Your endpoint URL includes the bucket name, which is incorrect.

## Current Configuration (INCORRECT):

```env
DO_SPACES_ENDPOINT=https://codenova-uploads.blr1.digitaloceanspaces.com
```

## Correct Configuration:

```env
DO_SPACES_KEY=DO00Z668...
DO_SPACES_SECRET=180SqeIo...
DO_SPACES_BUCKET=codenova-uploads
DO_SPACES_REGION=blr1
DO_SPACES_ENDPOINT=https://blr1.digitaloceanspaces.com
```

## Steps to Fix:

1. Open your `.env` file in the backend directory
2. Change the `DO_SPACES_ENDPOINT` line to:
   ```
   DO_SPACES_ENDPOINT=https://blr1.digitaloceanspaces.com
   ```
3. Save the file
4. Run the test again: `python test_spaces_connection.py`

## Why This Matters:

- The endpoint URL should only contain the region (blr1)
- The bucket name (codenova-uploads) is specified separately in DO_SPACES_BUCKET
- The boto3 client automatically constructs the full URL when making requests

After making this change, your file uploads to Digital Ocean Spaces should work correctly.
