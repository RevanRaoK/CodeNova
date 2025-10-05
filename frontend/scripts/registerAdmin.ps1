# PowerShell script to register admin user via API
# Usage: .\registerAdmin.ps1

$API_BASE_URL = "http://localhost:8000"

$adminCredentials = @{
    email = "revankokkirala@gmail.com"
    password = "Test@123"
    full_name = "Revan Kokkirala"
    role = "admin"
} | ConvertTo-Json

Write-Host "🚀 Admin Registration Script" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host "🔄 Registering admin user..." -ForegroundColor Yellow
Write-Host "Email: revankokkirala@gmail.com" -ForegroundColor Cyan
Write-Host "Role: admin" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "$API_BASE_URL/auth/register" -Method POST -Body $adminCredentials -ContentType "application/json"
    
    Write-Host "✅ Admin user registered successfully!" -ForegroundColor Green
    Write-Host "User ID: $($response.user.id)" -ForegroundColor Cyan
    Write-Host "Email: $($response.user.email)" -ForegroundColor Cyan
    Write-Host "Role: $($response.user.role)" -ForegroundColor Cyan
    
    if ($response.token) {
        Write-Host "Token: Generated" -ForegroundColor Cyan
    }
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    
    Write-Host "❌ Registration failed:" -ForegroundColor Red
    Write-Host "Status: $statusCode" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($statusCode -eq 409) {
        Write-Host "💡 User might already exist. You can try logging in with these credentials." -ForegroundColor Yellow
    }
    
    Write-Host "💡 Make sure your backend server is running on $API_BASE_URL" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Alternative curl command:" -ForegroundColor Yellow
Write-Host "curl -X POST `"http://localhost:8000/auth/register`"" -ForegroundColor Gray
Write-Host "  -H `"Content-Type: application/json`"" -ForegroundColor Gray
Write-Host "  -d `"{\`"email\`": \`"revankokkirala@gmail.com\`", \`"password\`": \`"Test@123\`", \`"full_name\`": \`"Revan Kokkirala\`", \`"role\`": \`"admin\`"}`"" -ForegroundColor Gray