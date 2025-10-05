/**
 * Debug the 422 validation error
 * Usage: node testLoginDebug.js
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

async function testLoginDebug() {
     const credentials = {
          email: 'revankokkirala@gmail.com',
          password: 'Test@123'
     };

     console.log('🔍 Debugging 422 validation error...');
     console.log('Request body:', JSON.stringify(credentials, null, 2));

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

          if (response.status === 422) {
               console.log('\n🔍 Validation errors:');
               if (data.detail && Array.isArray(data.detail)) {
                    data.detail.forEach(error => {
                         console.log(`  - Field: ${error.loc?.join('.')}`);
                         console.log(`  - Error: ${error.msg}`);
                         console.log(`  - Type: ${error.type}`);
                         console.log(`  - Input: ${JSON.stringify(error.input)}`);
                         console.log('');
                    });
               }
          }
     } catch (error) {
          console.error('❌ Network error:', error.message);
     }
}

async function testOriginalLogin() {
     console.log('\n🔄 Testing original login endpoint...');

     const formData = new URLSearchParams();
     formData.append('username', 'revankokkirala@gmail.com');
     formData.append('password', 'Test@123');

     try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
               },
               body: formData
          });

          console.log('Original login status:', response.status);
          const data = await response.json();
          console.log('Original login data:', JSON.stringify(data, null, 2));
     } catch (error) {
          console.error('❌ Original login error:', error.message);
     }
}

async function main() {
     await testLoginDebug();
     await testOriginalLogin();
}

main();