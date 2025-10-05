/**
 * Script to test backend connectivity and register admin
 * Usage: node testBackend.js
 */

const API_BASE_URL = 'http://localhost:8000'; // Adjust this to your backend URL

async function testBackendConnection() {
     console.log('🔍 Testing backend connection...');

     try {
          const response = await fetch(`${API_BASE_URL}/health`, {
               method: 'GET',
          });

          if (response.ok) {
               console.log('✅ Backend is running and accessible');
               return true;
          } else {
               console.log('⚠️ Backend responded but with status:', response.status);
               return false;
          }
     } catch (error) {
          console.log('❌ Backend is not accessible:', error.message);
          console.log('💡 Make sure your backend server is running on', API_BASE_URL);
          return false;
     }
}

async function registerAdminUser() {
     const adminData = {
          email: 'revankokkirala@gmail.com',
          password: 'Test@123',
          full_name: 'Revan Kokkirala',
          role: 'admin'
     };

     console.log('\n🔄 Attempting to register admin user...');
     console.log('Email:', adminData.email);

     try {
          const response = await fetch(`${API_BASE_URL}/auth/register`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/json',
               },
               body: JSON.stringify(adminData)
          });

          const data = await response.json();

          if (response.ok) {
               console.log('✅ Admin user registered successfully!');
               console.log('User Details:');
               console.log('  - ID:', data.user?.id);
               console.log('  - Email:', data.user?.email);
               console.log('  - Name:', data.user?.full_name);
               console.log('  - Role:', data.user?.role);
               console.log('  - Token:', data.token ? '✓ Generated' : '✗ Not provided');
               return data;
          } else {
               console.log('❌ Registration failed');
               console.log('Status:', response.status);
               console.log('Error:', data.detail || data.message || 'Unknown error');

               if (response.status === 409 || response.status === 400) {
                    console.log('\n💡 User might already exist. Testing login...');
                    return await testLogin(adminData);
               }
               return null;
          }
     } catch (error) {
          console.error('❌ Network error during registration:', error.message);
          return null;
     }
}

async function testLogin(credentials) {
     console.log('🔄 Testing login with existing credentials...');

     try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/json',
               },
               body: JSON.stringify({
                    email: credentials.email,
                    password: credentials.password
               })
          });

          const data = await response.json();

          if (response.ok) {
               console.log('✅ Login successful!');
               console.log('User Details:');
               console.log('  - ID:', data.user?.id);
               console.log('  - Email:', data.user?.email);
               console.log('  - Name:', data.user?.full_name);
               console.log('  - Role:', data.user?.role);

               if (data.user?.role === 'admin' || data.user?.role === 'team_lead') {
                    console.log('✅ User has admin privileges!');
               } else {
                    console.log('⚠️ User does not have admin privileges. Current role:', data.user?.role);
                    console.log('💡 You may need to update the user role to admin manually.');
               }

               return data;
          } else {
               console.log('❌ Login failed');
               console.log('Status:', response.status);
               console.log('Error:', data.detail || data.message || 'Invalid credentials');
               return null;
          }
     } catch (error) {
          console.error('❌ Network error during login:', error.message);
          return null;
     }
}

async function main() {
     console.log('🚀 Backend Test & Admin Registration');
     console.log('====================================');

     // Test backend connection
     const isBackendRunning = await testBackendConnection();

     if (!isBackendRunning) {
          console.log('\n❌ Cannot proceed without backend connection');
          console.log('Please start your backend server and try again.');
          return;
     }

     // Try to register admin user
     const result = await registerAdminUser();

     if (result) {
          console.log('\n🎉 Setup complete! You can now:');
          console.log('1. Go to http://localhost:5173/admin/login');
          console.log('2. Use the credentials:');
          console.log('   - Email: revankokkirala@gmail.com');
          console.log('   - Password: Test@123');
          console.log('3. Or click "Demo Admin Login" button');
     } else {
          console.log('\n❌ Setup failed. Please check your backend server and try again.');
     }
}

// Run the main function
main().catch(console.error);