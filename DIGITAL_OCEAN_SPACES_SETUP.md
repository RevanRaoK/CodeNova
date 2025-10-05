# Digital Ocean Spaces Setup Guide

This guide provides complete instructions for setting up Digital Ocean Spaces integration for file storage in the platform.

## Prerequisites

- Digital Ocean account
- Python environment with pip
- Access to the backend application configuration

## Step 1: Create Digital Ocean Spaces

1. **Log in to Digital Ocean Console**

   - Go to [Digital Ocean Console](https://cloud.digitalocean.com/)
   - Navigate to "Spaces Object Storage" in the left sidebar

2. **Create a New Space**

   - Click "Create a Space"
   - Choose a datacenter region (recommend same region as your application)
   - Choose a unique space name (e.g., `your-app-files`)
   - Set File Listing to "Restricted" for security
   - Click "Create a Space"

3. **Note Your Space Details**
   - Space Name: `your-space-name`
   - Endpoint: `https://your-space-name.region.digitaloceanspaces.com`
   - Region: `region` (e.g., `nyc3`, `sfo3`, `ams3`)

## Step 2: Generate API Keys

1. **Create Spaces Access Keys**
   - In Digital Ocean Console, go to "API" in the left sidebar
   - Click on "Spaces Keys" tab
   - Click "Generate New Key"
   - Give it a descriptive name (e.g., `your-app-spaces-key`)
   - Copy and securely store:
     - **Access Key ID** (similar to AWS Access Key)
     - **Secret Access Key** (similar to AWS Secret Key)

## Step 3: Install Required Dependencies

Add the following dependencies to your `requirements.txt`:

```txt
# Digital Ocean Spaces (S3-compatible)
boto3==1.35.0
botocore==1.35.0
```

Install the dependencies:

```bash
pip install boto3 botocore
```

## Step 4: Environment Configuration

Add the following environment variables to your `.env` file:

```env
# Digital Ocean Spaces Configuration
DO_SPACES_KEY=your_access_key_id_here
DO_SPACES_SECRET=your_secret_access_key_here
DO_SPACES_BUCKET=your-space-name
DO_SPACES_REGION=your-region
DO_SPACES_ENDPOINT=https://your-region.digitaloceanspaces.com

# File Storage Settings
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_EXTENSIONS=.py,.js,.ts,.java,.cpp,.c,.h,.css,.html,.json,.xml,.yaml,.yml,.md,.txt
FILE_UPLOAD_PATH=uploads/
SIGNED_URL_EXPIRATION_HOURS=24
```

## Step 5: Configure CORS (Optional)

If you need to upload files directly from the frontend:

1. **In Digital Ocean Console**
   - Go to your Space
   - Click on "Settings" tab
   - Scroll to "CORS Configurations"
   - Add a new CORS rule:

```json
{
  "AllowedOrigins": ["https://yourdomain.com", "http://localhost:3000"],
  "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
  "AllowedHeaders": ["*"],
  "MaxAgeSeconds": 3000
}
```

## Step 6: Test the Configuration

Create a test script to verify your setup:

```python
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

def test_spaces_connection():
    """Test Digital Ocean Spaces connection"""
    try:
        # Initialize the client
        session = boto3.session.Session()
        client = session.client(
            's3',
            region_name=os.getenv('DO_SPACES_REGION'),
            endpoint_url=os.getenv('DO_SPACES_ENDPOINT'),
            aws_access_key_id=os.getenv('DO_SPACES_KEY'),
            aws_secret_access_key=os.getenv('DO_SPACES_SECRET')
        )

        # Test connection by listing objects
        response = client.list_objects_v2(
            Bucket=os.getenv('DO_SPACES_BUCKET'),
            MaxKeys=1
        )

        print("✅ Successfully connected to Digital Ocean Spaces!")
        print(f"Bucket: {os.getenv('DO_SPACES_BUCKET')}")
        print(f"Region: {os.getenv('DO_SPACES_REGION')}")
        return True

    except ClientError as e:
        print(f"❌ Error connecting to Digital Ocean Spaces: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_spaces_connection()
```

Run the test:

```bash
python test_spaces_connection.py
```

## Step 7: Security Best Practices

1. **Environment Variables**

   - Never commit API keys to version control
   - Use environment variables or secure secret management
   - Rotate keys regularly

2. **Access Control**

   - Set appropriate bucket policies
   - Use IAM roles when possible
   - Implement proper authentication in your application

3. **File Validation**

   - Validate file types and sizes
   - Scan uploaded files for malware
   - Implement rate limiting for uploads

4. **Monitoring**
   - Monitor storage usage and costs
   - Set up alerts for unusual activity
   - Log all file operations

## Step 8: Production Considerations

1. **CDN Integration**

   - Consider using Digital Ocean CDN for better performance
   - Configure appropriate cache headers

2. **Backup Strategy**

   - Implement regular backups
   - Consider cross-region replication for critical files

3. **Cost Optimization**
   - Monitor storage usage
   - Implement lifecycle policies for old files
   - Use appropriate storage classes

## Troubleshooting

### Common Issues

1. **Connection Errors**

   - Verify API keys are correct
   - Check region and endpoint URL
   - Ensure network connectivity

2. **Permission Errors**

   - Verify API key has necessary permissions
   - Check bucket policies
   - Ensure correct bucket name

3. **Upload Failures**
   - Check file size limits
   - Verify CORS configuration
   - Check network timeouts

### Debug Commands

```bash
# Test AWS CLI with Digital Ocean Spaces
aws s3 ls --endpoint-url=https://your-region.digitaloceanspaces.com

# Upload test file
aws s3 cp test.txt s3://your-bucket/test.txt --endpoint-url=https://your-region.digitaloceanspaces.com
```

## Support

- [Digital Ocean Spaces Documentation](https://docs.digitalocean.com/products/spaces/)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [AWS S3 API Reference](https://docs.aws.amazon.com/s3/latest/API/Welcome.html)

## Example Environment File

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Digital Ocean Spaces
DO_SPACES_KEY=your_access_key_id
DO_SPACES_SECRET=your_secret_access_key
DO_SPACES_BUCKET=your-app-files
DO_SPACES_REGION=nyc3
DO_SPACES_ENDPOINT=https://nyc3.digitaloceanspaces.com

# File Storage
MAX_FILE_SIZE_MB=50
SIGNED_URL_EXPIRATION_HOURS=24
FILE_UPLOAD_PATH=uploads/

# Application
SECRET_KEY=your-secret-key
DEBUG=False
```

This setup guide covers all the necessary steps to integrate Digital Ocean Spaces with your application. Follow each step carefully and test the configuration before deploying to production.
