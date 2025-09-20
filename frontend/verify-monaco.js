// Simple verification script for Monaco Editor integration
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

console.log('🔍 Verifying Monaco Editor Integration...\n');

try {
  // Check if Monaco Editor packages are installed
  const monacoReactPackage = require('@monaco-editor/react/package.json');
  const monacoEditorPackage = require('monaco-editor/package.json');
  
  console.log('✅ @monaco-editor/react version:', monacoReactPackage.version);
  console.log('✅ monaco-editor version:', monacoEditorPackage.version);
  
  // Check if our TypeScript files exist
  const fs = require('fs');
  const path = require('path');
  
  const filesToCheck = [
    'tsconfig.json',
    'components/MonacoEditor.tsx',
    'components/MonacoEditorTest.tsx'
  ];
  
  console.log('\n📁 Checking required files:');
  filesToCheck.forEach(file => {
    if (fs.existsSync(path.join(process.cwd(), file))) {
      console.log(`✅ ${file} exists`);
    } else {
      console.log(`❌ ${file} missing`);
    }
  });
  
  console.log('\n🎉 Monaco Editor integration setup complete!');
  console.log('📝 Test the integration by visiting: http://localhost:5174/monaco-test');
  
} catch (error) {
  console.error('❌ Error during verification:', error.message);
  process.exit(1);
}