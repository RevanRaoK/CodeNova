# RabbitMQ Setup Guide for CodeNova

## Problem

The background workers are failing with:

```
ACCESS_REFUSED - Login was refused using authentication mechanism PLAIN
```

This means RabbitMQ is either:

1. Not installed
2. Not running
3. Has incorrect credentials configured

## Solution

### Step 1: Install RabbitMQ

#### Windows Installation:

1. **Download RabbitMQ:**

   - Go to: https://www.rabbitmq.com/download.html
   - Download "RabbitMQ Server for Windows"
   - Or use Chocolatey: `choco install rabbitmq`

2. **Install Erlang (Required):**

   - RabbitMQ needs Erlang to run
   - Download from: https://www.erlang.org/downloads
   - Or use Chocolatey: `choco install erlang`

3. **Install RabbitMQ:**
   - Run the installer
   - It will install as a Windows service

### Step 2: Start RabbitMQ Service

#### Using Windows Services:

```powershell
# Start RabbitMQ service
net start RabbitMQ

# Or using Services GUI:
# 1. Press Win + R
# 2. Type: services.msc
# 3. Find "RabbitMQ" service
# 4. Right-click → Start
```

#### Verify RabbitMQ is Running:

```powershell
# Check if RabbitMQ is listening on port 5672
netstat -an | findstr "5672"

# Should show: TCP  0.0.0.0:5672  LISTENING
```

### Step 3: Configure RabbitMQ Credentials

The default RabbitMQ credentials are:

- Username: `guest`
- Password: `guest`
- Host: `localhost`
- Port: `5672`

#### Check Your Backend Configuration:

Look at your `.env` file or `backend/app/core/config.py`:

```python
# Should have these settings:
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "guest"
RABBITMQ_PASSWORD = "guest"
RABBITMQ_VHOST = "/"
```

### Step 4: Enable RabbitMQ Management Plugin (Optional but Useful)

```powershell
# Enable management plugin
cd "C:\Program Files\RabbitMQ Server\rabbitmq_server-X.X.X\sbin"
.\rabbitmq-plugins.bat enable rabbitmq_management

# Restart RabbitMQ
net stop RabbitMQ
net start RabbitMQ
```

After enabling, access management UI at:

- URL: http://localhost:15672
- Username: guest
- Password: guest

### Step 5: Create CodeNova User (Recommended for Production)

```powershell
# Navigate to RabbitMQ sbin folder
cd "C:\Program Files\RabbitMQ Server\rabbitmq_server-X.X.X\sbin"

# Create new user
.\rabbitmqctl.bat add_user codenova codenova123

# Set permissions
.\rabbitmqctl.bat set_permissions -p / codenova ".*" ".*" ".*"

# Set as administrator
.\rabbitmqctl.bat set_user_tags codenova administrator
```

Then update your `.env`:

```env
RABBITMQ_USER=codenova
RABBITMQ_PASSWORD=codenova123
```

---

## Alternative: Use Docker (Easiest!)

If you have Docker installed:

```powershell
# Pull and run RabbitMQ with management
docker run -d --name rabbitmq `
  -p 5672:5672 `
  -p 15672:15672 `
  -e RABBITMQ_DEFAULT_USER=guest `
  -e RABBITMQ_DEFAULT_PASS=guest `
  rabbitmq:3-management

# Check if running
docker ps
```

Management UI: http://localhost:15672

---

## Verify Setup

### 1. Check RabbitMQ is Running:

```powershell
# Windows Service
Get-Service RabbitMQ

# Or check port
netstat -an | findstr "5672"
```

### 2. Test Connection:

```python
# Create test file: test_rabbitmq.py
import pika

try:
    credentials = pika.PlainCredentials('guest', 'guest')
    parameters = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    print("✅ RabbitMQ connection successful!")
    connection.close()
except Exception as e:
    print(f"❌ RabbitMQ connection failed: {e}")
```

Run: `python test_rabbitmq.py`

### 3. Start Workers:

```powershell
cd backend
conda activate base
python start_hybrid_queue.py
```

You should see:

```
✅ Connected to RabbitMQ successfully
✅ Worker started
Waiting for tasks...
```

---

## Common Issues

### Issue 1: "Connection refused"

**Solution:** RabbitMQ service not running

```powershell
net start RabbitMQ
```

### Issue 2: "ACCESS_REFUSED - Login was refused"

**Solutions:**

1. Check credentials in `.env` file
2. Default is `guest:guest`
3. `guest` user only works on localhost
4. Create new user if accessing remotely

### Issue 3: "Port 5672 already in use"

**Solution:** Another instance is running

```powershell
# Find process using port 5672
netstat -ano | findstr "5672"

# Kill the process (replace <PID> with actual process ID)
taskkill /F /PID <PID>
```

### Issue 4: Erlang not found

**Solution:** Install Erlang before RabbitMQ

- Download: https://www.erlang.org/downloads
- Or: `choco install erlang`

---

## Quick Start (TL;DR)

```powershell
# 1. Install (if not installed)
choco install erlang rabbitmq

# 2. Start service
net start RabbitMQ

# 3. Verify
netstat -an | findstr "5672"

# 4. Start workers
cd backend
conda activate base
python start_hybrid_queue.py

# 5. Trigger analysis
# Click "Analyze Repository" in UI
```

---

## Environment Variables

Make sure your `backend/.env` has:

```env
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

# Redis Configuration (if also needed)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

---

## After RabbitMQ is Running

1. **Start Backend Server:**

   ```powershell
   cd backend
   conda activate base
   uvicorn app.main:app --reload
   ```

2. **Start Workers (separate terminal):**

   ```powershell
   cd backend
   conda activate base
   python start_hybrid_queue.py
   ```

3. **Trigger Analysis:**

   - Go to UI
   - Click "Analyze Repository"
   - Watch the workers terminal for progress
   - Analysis will complete in 1-5 minutes

4. **View Results:**
   - Click refresh button in UI
   - Status will show "completed"
   - Issues count will be displayed
   - Click on the analysis to see details

---

## Success Indicators

✅ **RabbitMQ Running:**

```
RabbitMQ service is running
Port 5672 is listening
```

✅ **Workers Connected:**

```
Connected to RabbitMQ successfully
Worker started
Waiting for tasks...
```

✅ **Analysis Processing:**

```
Starting repository analysis for <repo_id>
Fetching files from GitHub
Discovered 45 files
Analyzing file 1/45...
```

✅ **Analysis Complete:**

```
Repository analysis completed
43 files analyzed, 28 issues found
```

---

## Need Help?

If you get stuck:

1. Check Windows Event Viewer for RabbitMQ errors
2. Check RabbitMQ logs in: `C:\Users\<YourUser>\AppData\Roaming\RabbitMQ\log`
3. Use Management UI to see connections: http://localhost:15672
4. Check firewall isn't blocking port 5672

Good luck! 🚀
