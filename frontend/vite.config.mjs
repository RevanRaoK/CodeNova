export default async () => {
  const { defineConfig } = await import('vite');
  const react = (await import('@vitejs/plugin-react')).default;
  const tailwindcss = (await import('@tailwindcss/vite')).default;
  const { transformWithEsbuild } = await import('vite');

  return defineConfig({
    plugins: [
      tailwindcss(),
      {
        name: 'treat-js-files-as-jsx',
        async transform(code, id) {
          if (!id.match(/src\/.*\.js$/)) return null;
          return transformWithEsbuild(code, id, {
            loader: 'jsx',
            jsx: 'automatic',
          });
        },
      },
      react(),
    ],
    optimizeDeps: {
      force: true,
      include: [
        '@monaco-editor/react',
        'react',
        'react-dom',
        'react-router-dom',
        'axios'
      ],
      exclude: ['monaco-editor'],
      esbuildOptions: {
        loader: {
          '.js': 'jsx',
        },
      },
    },
    build: {
      target: 'es2020',
      minify: 'esbuild',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            // Monaco Editor and related chunks
            'monaco-editor': ['monaco-editor'],
            'monaco-react': ['@monaco-editor/react'],
            
            // React and core libraries
            'react-vendor': ['react', 'react-dom'],
            'router': ['react-router-dom'],
            
            // UI and utility libraries
            'ui-libs': ['lucide-react', 'recharts'],
            'utils': ['axios'],
          },
          // Optimize chunk sizes
          chunkFileNames: (chunkInfo) => {
            const facadeModuleId = chunkInfo.facadeModuleId ? chunkInfo.facadeModuleId.split('/').pop() : 'chunk';
            return `assets/[name]-[hash].js`;
          },
        },
      },
      // Increase chunk size warning limit for Monaco Editor
      chunkSizeWarningLimit: 1000,
    },
    define: {
      global: 'globalThis',
    },
    worker: {
      format: 'es',
    },
    // Performance optimizations
    esbuild: {
      drop: ['console', 'debugger'], // Remove console.log and debugger in production
    },
  });
};
