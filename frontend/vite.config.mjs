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
        'axios',
        'recharts',
        'lucide-react'
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
      sourcemap: process.env.NODE_ENV === 'development',
      cssCodeSplit: true,
      rollupOptions: {
        output: {
          manualChunks: (id) => {
            // Vendor chunks for better caching
            if (id.includes('node_modules')) {
              // Monaco Editor - separate chunk due to size
              if (id.includes('monaco-editor')) {
                return 'monaco-editor';
              }
              if (id.includes('@monaco-editor/react')) {
                return 'monaco-react';
              }

              // React ecosystem
              if (id.includes('react') || id.includes('react-dom')) {
                return 'react-vendor';
              }
              if (id.includes('react-router')) {
                return 'router';
              }

              // Charts and visualization
              if (id.includes('recharts') || id.includes('d3-')) {
                return 'charts';
              }

              // UI libraries
              if (id.includes('lucide-react')) {
                return 'icons';
              }

              // HTTP and utilities
              if (id.includes('axios')) {
                return 'http';
              }

              // OAuth and auth
              if (id.includes('@react-oauth') || id.includes('oauth')) {
                return 'auth';
              }

              // Other vendor libraries
              return 'vendor';
            }

            // Application chunks based on features
            if (id.includes('/components/admin/')) {
              return 'admin';
            }
            if (id.includes('/components/analytics/')) {
              return 'analytics';
            }
            if (id.includes('/components/github/')) {
              return 'github';
            }
            if (id.includes('/components/feedback/')) {
              return 'feedback';
            }
            if (id.includes('/components/file/')) {
              return 'file-management';
            }
            if (id.includes('/pages/')) {
              return 'pages';
            }
          },
          // Optimize chunk and asset naming
          chunkFileNames: (chunkInfo) => {
            return `assets/js/[name]-[hash].js`;
          },
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.');
            const ext = info[info.length - 1];
            if (/\.(css)$/.test(assetInfo.name)) {
              return `assets/css/[name]-[hash].${ext}`;
            }
            if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico)$/i.test(assetInfo.name)) {
              return `assets/images/[name]-[hash].${ext}`;
            }
            if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name)) {
              return `assets/fonts/[name]-[hash].${ext}`;
            }
            return `assets/[name]-[hash].${ext}`;
          },
        },
        // External dependencies that should not be bundled
        external: (id) => {
          // Keep monaco-editor workers external for proper loading
          return id.includes('monaco-editor/esm/vs/') && id.includes('.worker');
        },
      },
      // Optimize chunk sizes
      chunkSizeWarningLimit: 1000,
      // Optimize assets
      assetsInlineLimit: 4096, // Inline assets smaller than 4kb
    },
    define: {
      global: 'globalThis',
      // Remove development-only code in production
      __DEV__: process.env.NODE_ENV === 'development',
    },
    worker: {
      format: 'es',
    },
    // Performance optimizations
    esbuild: {
      // Remove console and debugger in production
      drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : [],
      // Optimize for modern browsers in production
      target: process.env.NODE_ENV === 'production' ? 'es2020' : 'es2017',
      // Enable tree shaking
      treeShaking: true,
    },
    // Server configuration for development
    server: {
      // Enable HTTP/2 for better performance
      https: false,
      // Optimize HMR
      hmr: {
        overlay: true,
      },
      // Preload modules
      warmup: {
        clientFiles: [
          './src/main.tsx',
          './src/App.jsx',
          './src/components/**/*.{jsx,tsx}',
          './src/pages/**/*.{jsx,tsx}',
        ],
      },
    },
    // Preview configuration
    preview: {
      port: 3000,
      strictPort: true,
    },
  });
};
