@echo off
echo 🚀 Admin Registration Script
echo ============================
echo 🔄 Registering admin user...
echo Email: revankokkirala@gmail.com
echo Role: admin
echo.

curl -X POST "http://localhost:8000/auth/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"revankokkirala@gmail.com\", \"password\": \"Test@123\", \"full_name\": \"Revan Kokkirala\", \"role\": \"admin\"}"

echo.
echo ✅ Registration attempt completed!
echo 💡 If you see a success response above, you can now login at:
echo    http://localhost:5173/admin/login
echo.
pause