/**
 * Test the new JSON login endpoint
 * Usage: node testNewLogin.js
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

async function testNewJsonLogin() {
     const credentials = {
          email: 'revankokkirala@gmail.com',
          password: 'Test@123'
     };

     console.log('🔄 Testing new JSON login endpoint...');
     console.log('Email:', credentials.email);
     console.log('API URL:', `${API_BASE_URL}/auth/login-json`);

     try {
          const response = await fetch(`${API_BASE_URL}/auth/login-json`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/json',
               },
               body: JSON.stringify(credentials)
          });

          console.log('Response status:', response.status);
          console.log('Response headers:', Object.fromEntries(response.headers.entries()));

          const data = await response.json();
          console.log('Response data:', JSON.stringify(data, null, 2));

          if (response.ok) {
               console.log('\n✅ Login successful!');
               console.log('User ID:', data.user?.id);
               console.log('User Email:', data.user?.email);
               console.log('User Name:', data.user?.full_name);
               console.log('User Role:', data.user?.role);
               console.log('User Active:', data.user?.is_active);
               console.log('Access Token:', data.access_token ? 'Present' : 'Missing');

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

testNewJsonLogin();