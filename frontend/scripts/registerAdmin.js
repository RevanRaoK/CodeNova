/**
 * Script to register an admin user via API
 * Usage: node registerAdmin.js
 */

const API_BASE_URL = 'http://localhost:8000'; // Adjust this to your backend URL

const adminCredentials = {
     email: 'revankokkirala@gmail.com',
     password: 'Test@123',
     full_name: 'Revan Kokkirala',
     role: 'admin'
};

async function registerAdmin() {
     try {
          console.log('🔄 Registering admin user...');
          console.log('Email:', adminCredentials.email);
          console.log('Role:', adminCredentials.role);

          const response = await fetch(`${API_BASE_URL}/auth/register`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/json',
               },
               body: JSON.stringify(adminCredentials)
          });

          const data = await response.json();

          if (response.ok) {
               console.log('✅ Admin user registered successfully!');
               console.log('User ID:', data.user?.id);
               console.log('Email:', data.user?.email);
               console.log('Role:', data.user?.role);
               console.log('Token:', data.token ? 'Generated' : 'Not provided');
          } else {
               console.error('❌ Registration failed:');
               console.error('Status:', response.status);
               console.error('Error:', data.detail || data.message || 'Unknown error');

               if (response.status === 409) {
                    console.log('💡 User might already exist. Trying to update role...');
                    await updateUserRole();
               }
          }
     } catch (error) {
          console.error('❌ Network error:', error.message);
          console.log('💡 Make sure your backend server is running on', API_BASE_URL);
     }
}

async function updateUserRole() {
     try {
          // First, try to login to get admin token
          const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
               method: 'POST',
               headers: {
                    'Content-Type': 'application/json',
               },
               body: JSON.stringify({
                    email: adminCredentials.email,
                    password: adminCredentials.password
               })
          });

          if (loginResponse.ok) {
               const loginData = await loginResponse.json();
               const token = loginData.token;
               const userId = loginData.user?.id;

               if (userId && token) {
                    // Update user role to admin
                    const updateResponse = await fetch(`${API_BASE_URL}/admin/users/${userId}/role`, {
                         method: 'PUT',
                         headers: {
                              'Content-Type': 'application/json',
                              'Authorization': `Bearer ${token}`
                         },
                         body: JSON.stringify({
                              role: 'admin'
                         })
                    });

                    if (updateResponse.ok) {
                         console.log('✅ User role updated to admin successfully!');
                    } else {
                         const updateData = await updateResponse.json();
                         console.error('❌ Role update failed:', updateData.detail || 'Unknown error');
                    }
               }
          } else {
               console.log('❌ Could not login with existing credentials');
          }
     } catch (error) {
          console.error('❌ Error updating role:', error.message);
     }
}

// Alternative method using curl command
function generateCurlCommand() {
     const curlCommand = `curl -X POST "${API_BASE_URL}/auth/register" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "${adminCredentials.email}",
    "password": "${adminCredentials.password}",
    "full_name": "${adminCredentials.full_name}",
    "role": "${adminCredentials.role}"
  }'`;

     console.log('\n📋 Alternative: Run this curl command:');
     console.log(curlCommand);
}

// Run the registration
console.log('🚀 Admin Registration Script');
console.log('==========================');
registerAdmin();
generateCurlCommand();