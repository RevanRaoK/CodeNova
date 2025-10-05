/**
 * Script to discover available API endpoints
 * Usage: node discoverAPI.js
 */

const API_BASE_URL = 'http://localhost:8000';

async function testEndpoint(endpoint, method = 'GET') {
     try {
          const response = await fetch(`${API_BASE_URL}${endpoint}`, {
               method: method,
               headers: {
                    'Content-Type': 'application/json',
               }
          });

          return {
               endpoint,
               method,
               status: response.status,
               ok: response.ok,
               statusText: response.statusText
          };
     } catch (error) {
          return {
               endpoint,
               method,
               status: 'ERROR',
               ok: false,
               error: error.message
          };
     }
}

async function discoverEndpoints() {
     console.log('🔍 Discovering API endpoints...');
     console.log('================================');

     const commonEndpoints = [
          '/',
          '/health',
          '/docs',
          '/api',
          '/api/v1',
          '/auth',
          '/auth/login',
          '/auth/register',
          '/auth/signup',
          '/users',
          '/users/register',
          '/users/login',
          '/admin',
          '/admin/users',
          '/register',
          '/login',
          '/signup'
     ];

     console.log('Testing common endpoints...\n');

     for (const endpoint of commonEndpoints) {
          const result = await testEndpoint(endpoint);
          const statusColor = result.ok ? '✅' : result.status === 404 ? '❌' : '⚠️';
          console.log(`${statusColor} ${result.method} ${endpoint} → ${result.status} ${result.statusText || result.error || ''}`);
     }

     console.log('\n🔍 Testing POST endpoints...\n');

     const postEndpoints = [
          '/auth/login',
          '/auth/register',
          '/users/login',
          '/users/register',
          '/login',
          '/register',
          '/signup'
     ];

     for (const endpoint of postEndpoints) {
          const result = await testEndpoint(endpoint, 'POST');
          const statusColor = result.status === 422 || result.status === 400 ? '✅' : result.status === 404 ? '❌' : '⚠️';
          console.log(`${statusColor} POST ${endpoint} → ${result.status} ${result.statusText || result.error || ''}`);
     }
}

async function testRootEndpoint() {
     console.log('\n🔍 Testing root endpoint for API info...\n');

     try {
          const response = await fetch(`${API_BASE_URL}/`);
          const text = await response.text();

          console.log('Root endpoint response:');
          console.log('Status:', response.status);
          console.log('Content-Type:', response.headers.get('content-type'));
          console.log('Body:', text.substring(0, 500) + (text.length > 500 ? '...' : ''));

          // Try to parse as JSON
          try {
               const json = JSON.parse(text);
               console.log('\nParsed JSON:', json);
          } catch (e) {
               console.log('\nResponse is not JSON');
          }
     } catch (error) {
          console.log('Error testing root endpoint:', error.message);
     }
}

async function main() {
     console.log('🚀 API Discovery Tool');
     console.log('====================');
     console.log('Backend URL:', API_BASE_URL);
     console.log('');

     await testRootEndpoint();
     await discoverEndpoints();

     console.log('\n💡 Tips:');
     console.log('- ✅ = Endpoint exists and responds');
     console.log('- ⚠️ = Endpoint exists but may need authentication/data');
     console.log('- ❌ = Endpoint not found (404)');
     console.log('- Status 422/400 on POST usually means endpoint exists but needs data');
}

main().catch(console.error);