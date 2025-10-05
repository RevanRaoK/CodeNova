/**
 * Test login with correct OAuth2 form format
 * Usage: node testLoginForm.js
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

async function testLoginWithForm() {
     const credentials = {
          username: 'revankokkirala@gmail.com', // OAuth2 uses 'username' field
          password: 'Test@123'
     };

     console.log('🔄 Testing login with OAuth2 form format...');
     console.log('Username:', credentials.username);
     console.log('API URL:', `${API_BASE_URL}/auth/login`);

     try {
          // Create form data (OAuth2PasswordRequestForm expects form data)
          const formData = new URLSearchParams();
          formData.append('username', credentials.username);
          formData.append('password', credentials.password);

          const response = await fetch(`${API_BASE_URL}/auth/login`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
               },
               body: formData
          });

          console.log('Response status:', response.status);
          console.log('Response headers:', Object.fromEntries(response.headers.entries()));

          const data = await response.json();
          console.log('Response data:', JSON.stringify(data, null, 2));

          if (response.ok) {
               console.log('\n✅ Login successful!');
               console.log('User:', data.user);
               console.log('Token:', data.access_token ? 'Present' : 'Missing');

               if (data.user && (data.user.role === 'admin' || data.user.role === 'team_lead')) {
                    console.log('✅ User has admin privileges!');
               } else {
                    console.log('❌ User does not have admin privileges');
                    console.log('User role:', data.user?.role);
               }
          } else {
               console.log('\n❌ Login failed');
               console.log('Error:', data.detail || data.message || 'Unknown error');
          }
     } catch (error) {
          console.error('❌ Network error:', error.message);
     }
}

async function testLoginWithJSON() {
     const credentials = {
          email: 'revankokkirala@gmail.com',
          password: 'Test@123'
     };

     console.log('\n🔄 Testing login with JSON format...');
     console.log('Email:', credentials.email);

     try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/json',
               },
               body: JSON.stringify(credentials)
          });

          console.log('Response status:', response.status);
          const data = await response.json();
          console.log('Response data:', JSON.stringify(data, null, 2));

          if (response.ok) {
               console.log('✅ JSON login also works!');
          } else {
               console.log('❌ JSON login failed:', data.detail);
          }
     } catch (error) {
          console.error('❌ JSON login error:', error.message);
     }
}

async function main() {
     await testLoginWithForm();
     await testLoginWithJSON();
}

main();