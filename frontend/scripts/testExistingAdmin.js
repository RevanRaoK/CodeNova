/**
 * Test login with existing admin user
 * Usage: node testExistingAdmin.js
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

async function testExistingAdmin() {
     // Try the existing admin user from database
     const credentials = {
          email: 'test@example.com',
          password: 'password' // Common default password
     };

     console.log('🔄 Testing existing admin user...');
     console.log('Email:', credentials.email);
     console.log('API URL:', `${API_BASE_URL}/auth/login-json`);

     const passwordsToTry = [
          'password',
          'admin',
          'test',
          'test123',
          'Test@123',
          '123456'
     ];

     for (const password of passwordsToTry) {
          console.log(`\\n🔑 Trying password: ${password}`);

          try {
               const response = await fetch(`${API_BASE_URL}/auth/login-json`, {
                    method: 'POST',
                    headers: {
                         'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                         email: credentials.email,
                         password: password
                    })
               });

               const data = await response.json();

               if (response.ok) {
                    console.log('✅ Login successful!');
                    console.log('User:', data.user);
                    console.log('Role:', data.user?.role);
                    console.log('Token:', data.access_token ? 'Present' : 'Missing');

                    console.log('\\n🎉 Found working credentials:');
                    console.log(`Email: ${credentials.email}`);
                    console.log(`Password: ${password}`);
                    return;
               } else {
                    console.log(`❌ Failed: ${data.detail}`);
               }
          } catch (error) {
               console.log(`❌ Error: ${error.message}`);
          }
     }

     console.log('\\n❌ No working password found for test@example.com');
}

async function createNewAdminUser() {
     console.log('\\n🔄 Creating new admin user...');

     const userData = {
          email: 'revankokkirala@gmail.com',
          password: 'Test@123',
          full_name: 'Revan Kokkirala'
     };

     try {
          const response = await fetch(`${API_BASE_URL}/auth/register`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/json',
               },
               body: JSON.stringify(userData)
          });

          const data = await response.json();

          if (response.ok) {
               console.log('✅ User registered successfully!');
               console.log('User:', data.user);
               console.log('Role:', data.user?.role);

               if (data.user?.role !== 'admin') {
                    console.log('\\n⚠️ User created but role is not admin');
                    console.log('You can update the role in database:');
                    console.log(`UPDATE users SET role = 'ADMIN' WHERE email = 'revankokkirala@gmail.com';`);
               }

               return data;
          } else {
               console.log('❌ Registration failed');
               console.log('Status:', response.status);
               console.log('Error:', data.detail || 'Unknown error');
               return null;
          }
     } catch (error) {
          console.error('❌ Network error:', error.message);
          return null;
     }
}

async function main() {
     console.log('🚀 Testing Admin Login Options');
     console.log('==============================');

     // First try existing admin
     await testExistingAdmin();

     // Then try to create new user
     await createNewAdminUser();
}

main();