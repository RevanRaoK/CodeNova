#!/usr/bin/env node

/**
 * Frontend build optimization script
 * 
 * This script provides build optimization utilities for the React frontend,
 * including bundle analysis, performance monitoring, and optimization recommendations.
 * 
 * Requirements covered: Performance and scalability for all features
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class BuildOptimizer {
     constructor() {
          this.buildDir = path.join(__dirname, '..', 'dist');
          this.packageJson = require('../package.json');
     }

     /**
      * Analyze bundle sizes and provide optimization recommendations
      */
     analyzeBundleSize() {
          console.log('🔍 Analyzing bundle sizes...\n');

          if (!fs.existsSync(this.buildDir)) {
               console.error('❌ Build directory not found. Run "npm run build" first.');
               return;
          }

          const stats = this.getBundleStats();
          this.printBundleAnalysis(stats);
          this.generateOptimizationRecommendations(stats);
     }

     /**
      * Get bundle statistics
      */
     getBundleStats() {
          const stats = {
               totalSize: 0,
               jsFiles: [],
               cssFiles: [],
               assetFiles: [],
               chunks: {}
          };

          const walkDir = (dir, relativePath = '') => {
               const files = fs.readdirSync(dir);

               files.forEach(file => {
                    const filePath = path.join(dir, file);
                    const relativeFilePath = path.join(relativePath, file);
                    const stat = fs.statSync(filePath);

                    if (stat.isDirectory()) {
                         walkDir(filePath, relativeFilePath);
                    } else {
                         const size = stat.size;
                         stats.totalSize += size;

                         const ext = path.extname(file).toLowerCase();
                         const fileInfo = {
                              name: file,
                              path: relativeFilePath,
                              size: size,
                              sizeKB: Math.round(size / 1024 * 100) / 100,
                              sizeMB: Math.round(size / (1024 * 1024) * 100) / 100
                         };

                         if (ext === '.js') {
                              stats.jsFiles.push(fileInfo);

                              // Identify chunk types
                              if (file.includes('vendor')) {
                                   stats.chunks.vendor = (stats.chunks.vendor || 0) + size;
                              } else if (file.includes('monaco')) {
                                   stats.chunks.monaco = (stats.chunks.monaco || 0) + size;
                              } else if (file.includes('react')) {
                                   stats.chunks.react = (stats.chunks.react || 0) + size;
                              } else {
                                   stats.chunks.app = (stats.chunks.app || 0) + size;
                              }
                         } else if (ext === '.css') {
                              stats.cssFiles.push(fileInfo);
                         } else {
                              stats.assetFiles.push(fileInfo);
                         }
                    }
               });
          };

          walkDir(this.buildDir);

          // Sort files by size (largest first)
          stats.jsFiles.sort((a, b) => b.size - a.size);
          stats.cssFiles.sort((a, b) => b.size - a.size);
          stats.assetFiles.sort((a, b) => b.size - a.size);

          return stats;
     }

     /**
      * Print bundle analysis results
      */
     printBundleAnalysis(stats) {
          console.log('📊 Bundle Analysis Results');
          console.log('='.repeat(50));

          console.log(`Total Bundle Size: ${(stats.totalSize / (1024 * 1024)).toFixed(2)} MB`);
          console.log(`JavaScript Files: ${stats.jsFiles.length}`);
          console.log(`CSS Files: ${stats.cssFiles.length}`);
          console.log(`Asset Files: ${stats.assetFiles.length}\n`);

          // Chunk breakdown
          console.log('📦 Chunk Breakdown:');
          Object.entries(stats.chunks).forEach(([chunk, size]) => {
               const sizeKB = (size / 1024).toFixed(2);
               const percentage = ((size / stats.totalSize) * 100).toFixed(1);
               console.log(`  ${chunk}: ${sizeKB} KB (${percentage}%)`);
          });
          console.log('');

          // Largest JavaScript files
          console.log('📄 Largest JavaScript Files:');
          stats.jsFiles.slice(0, 10).forEach((file, index) => {
               console.log(`  ${index + 1}. ${file.name} - ${file.sizeKB} KB`);
          });
          console.log('');

          // Largest CSS files
          if (stats.cssFiles.length > 0) {
               console.log('🎨 CSS Files:');
               stats.cssFiles.forEach((file, index) => {
                    console.log(`  ${index + 1}. ${file.name} - ${file.sizeKB} KB`);
               });
               console.log('');
          }
     }

     /**
      * Generate optimization recommendations
      */
     generateOptimizationRecommendations(stats) {
          console.log('💡 Optimization Recommendations');
          console.log('='.repeat(50));

          const recommendations = [];
          const totalSizeMB = stats.totalSize / (1024 * 1024);

          // Size-based recommendations
          if (totalSizeMB > 5) {
               recommendations.push('⚠️  Bundle size is large (>5MB). Consider code splitting and lazy loading.');
          }

          // JavaScript-specific recommendations
          const largestJSFile = stats.jsFiles[0];
          if (largestJSFile && largestJSFile.sizeMB > 1) {
               recommendations.push(`⚠️  Largest JS file (${largestJSFile.name}) is ${largestJSFile.sizeMB}MB. Consider splitting.`);
          }

          // Monaco Editor specific
          const monacoSize = stats.chunks.monaco || 0;
          if (monacoSize > 500 * 1024) { // > 500KB
               recommendations.push('📝 Monaco Editor is large. Ensure it\'s lazy loaded and only imported when needed.');
          }

          // Vendor chunk recommendations
          const vendorSize = stats.chunks.vendor || 0;
          if (vendorSize > 1024 * 1024) { // > 1MB
               recommendations.push('📦 Vendor chunk is large. Consider splitting vendor libraries further.');
          }

          // General recommendations
          recommendations.push('✅ Enable gzip compression on your server.');
          recommendations.push('✅ Use a CDN for static assets.');
          recommendations.push('✅ Implement service worker for caching.');
          recommendations.push('✅ Consider using dynamic imports for route-based code splitting.');

          if (recommendations.length === 0) {
               console.log('✅ Bundle size looks good! No major optimizations needed.');
          } else {
               recommendations.forEach(rec => console.log(rec));
          }
          console.log('');
     }

     /**
      * Run build performance test
      */
     runBuildPerformanceTest() {
          console.log('⚡ Running build performance test...\n');

          const startTime = Date.now();

          try {
               // Clean build
               console.log('🧹 Cleaning previous build...');
               if (fs.existsSync(this.buildDir)) {
                    fs.rmSync(this.buildDir, { recursive: true });
               }

               // Run build
               console.log('🔨 Building application...');
               execSync('npm run build', { stdio: 'pipe' });

               const buildTime = Date.now() - startTime;
               const buildTimeSeconds = (buildTime / 1000).toFixed(2);

               console.log(`✅ Build completed in ${buildTimeSeconds} seconds`);

               // Analyze the build
               this.analyzeBundleSize();

               // Performance recommendations
               this.generateBuildPerformanceRecommendations(buildTime);

          } catch (error) {
               console.error('❌ Build failed:', error.message);
          }
     }

     /**
      * Generate build performance recommendations
      */
     generateBuildPerformanceRecommendations(buildTime) {
          console.log('🚀 Build Performance Recommendations');
          console.log('='.repeat(50));

          const buildTimeSeconds = buildTime / 1000;

          if (buildTimeSeconds > 60) {
               console.log('⚠️  Build time is slow (>60s). Consider:');
               console.log('   - Using SWC instead of Babel');
               console.log('   - Enabling persistent caching');
               console.log('   - Reducing the number of dependencies');
          } else if (buildTimeSeconds > 30) {
               console.log('⚠️  Build time is moderate (>30s). Consider:');
               console.log('   - Enabling build caching');
               console.log('   - Optimizing import statements');
          } else {
               console.log('✅ Build time is good!');
          }

          console.log('\n🔧 General build optimizations:');
          console.log('   - Use esbuild for faster transpilation');
          console.log('   - Enable parallel processing');
          console.log('   - Optimize dependency resolution');
          console.log('   - Use build caching in CI/CD');
     }

     /**
      * Generate performance monitoring script
      */
     generatePerformanceMonitoring() {
          const monitoringScript = `
// Performance monitoring for production builds
(function() {
  if (typeof window === 'undefined' || !window.performance) return;

  // Core Web Vitals monitoring
  function measureCoreWebVitals() {
    // Largest Contentful Paint (LCP)
    new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('LCP:', lastEntry.startTime);
    }).observe({ entryTypes: ['largest-contentful-paint'] });

    // First Input Delay (FID)
    new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      entries.forEach((entry) => {
        console.log('FID:', entry.processingStart - entry.startTime);
      });
    }).observe({ entryTypes: ['first-input'] });

    // Cumulative Layout Shift (CLS)
    let clsValue = 0;
    new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      entries.forEach((entry) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      });
      console.log('CLS:', clsValue);
    }).observe({ entryTypes: ['layout-shift'] });
  }

  // Bundle loading performance
  function measureBundleLoading() {
    const resources = performance.getEntriesByType('resource');
    const jsResources = resources.filter(r => r.name.includes('.js'));
    const cssResources = resources.filter(r => r.name.includes('.css'));

    console.group('Bundle Loading Performance');
    console.log('JS files loaded:', jsResources.length);
    console.log('CSS files loaded:', cssResources.length);
    
    const totalJSSize = jsResources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
    const totalCSSSize = cssResources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
    
    console.log('Total JS size:', (totalJSSize / 1024).toFixed(2), 'KB');
    console.log('Total CSS size:', (totalCSSSize / 1024).toFixed(2), 'KB');
    console.groupEnd();
  }

  // Initialize monitoring
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      measureCoreWebVitals();
      measureBundleLoading();
    });
  } else {
    measureCoreWebVitals();
    measureBundleLoading();
  }
})();
`;

          const outputPath = path.join(__dirname, '..', 'public', 'performance-monitor.js');
          fs.writeFileSync(outputPath, monitoringScript);
          console.log('📊 Performance monitoring script generated at public/performance-monitor.js');
     }

     /**
      * Check for unused dependencies
      */
     checkUnusedDependencies() {
          console.log('🔍 Checking for unused dependencies...\n');

          try {
               // This would require a more sophisticated analysis
               // For now, we'll check for common unused packages
               const dependencies = Object.keys(this.packageJson.dependencies || {});
               const devDependencies = Object.keys(this.packageJson.devDependencies || {});

               console.log(`📦 Total dependencies: ${dependencies.length}`);
               console.log(`🛠️  Dev dependencies: ${devDependencies.length}`);

               // Check for potentially unused packages
               const potentiallyUnused = [];
               const commonUnused = [
                    'lodash', 'moment', 'jquery', 'bootstrap'
               ];

               dependencies.forEach(dep => {
                    if (commonUnused.includes(dep)) {
                         potentiallyUnused.push(dep);
                    }
               });

               if (potentiallyUnused.length > 0) {
                    console.log('\n⚠️  Potentially unused dependencies:');
                    potentiallyUnused.forEach(dep => {
                         console.log(`   - ${dep}`);
                    });
                    console.log('\n💡 Consider removing unused dependencies to reduce bundle size.');
               } else {
                    console.log('✅ No obviously unused dependencies found.');
               }

          } catch (error) {
               console.error('❌ Error checking dependencies:', error.message);
          }
     }

     /**
      * Generate optimization report
      */
     generateOptimizationReport() {
          console.log('📋 Generating comprehensive optimization report...\n');

          const report = {
               timestamp: new Date().toISOString(),
               bundleAnalysis: null,
               recommendations: [],
               performance: {}
          };

          // Run all checks
          if (fs.existsSync(this.buildDir)) {
               report.bundleAnalysis = this.getBundleStats();
          }

          // Generate report file
          const reportPath = path.join(__dirname, '..', 'optimization-report.json');
          fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

          console.log(`📄 Optimization report saved to: ${reportPath}`);

          // Generate human-readable report
          const readableReportPath = path.join(__dirname, '..', 'optimization-report.md');
          this.generateMarkdownReport(report, readableReportPath);

          console.log(`📖 Human-readable report saved to: ${readableReportPath}`);
     }

     /**
      * Generate markdown report
      */
     generateMarkdownReport(report, outputPath) {
          let markdown = `# Frontend Optimization Report

Generated: ${report.timestamp}

## Bundle Analysis

`;

          if (report.bundleAnalysis) {
               const stats = report.bundleAnalysis;
               markdown += `- **Total Size**: ${(stats.totalSize / (1024 * 1024)).toFixed(2)} MB
- **JavaScript Files**: ${stats.jsFiles.length}
- **CSS Files**: ${stats.cssFiles.length}
- **Asset Files**: ${stats.assetFiles.length}

### Largest Files

`;
               stats.jsFiles.slice(0, 5).forEach((file, index) => {
                    markdown += `${index + 1}. ${file.name} - ${file.sizeKB} KB\n`;
               });
          }

          markdown += `
## Recommendations

- Enable gzip compression
- Use CDN for static assets
- Implement service worker caching
- Consider code splitting for large components
- Optimize images and assets
- Use lazy loading for non-critical components

## Performance Checklist

- [ ] Bundle size < 5MB
- [ ] Largest JS file < 1MB
- [ ] Gzip compression enabled
- [ ] CDN configured
- [ ] Service worker implemented
- [ ] Code splitting implemented
- [ ] Lazy loading implemented
- [ ] Performance monitoring added
`;

          fs.writeFileSync(outputPath, markdown);
     }
}

// CLI interface
function main() {
     const optimizer = new BuildOptimizer();
     const command = process.argv[2];

     switch (command) {
          case 'analyze':
               optimizer.analyzeBundleSize();
               break;
          case 'test':
               optimizer.runBuildPerformanceTest();
               break;
          case 'monitor':
               optimizer.generatePerformanceMonitoring();
               break;
          case 'deps':
               optimizer.checkUnusedDependencies();
               break;
          case 'report':
               optimizer.generateOptimizationReport();
               break;
          default:
               console.log(`
🚀 Frontend Build Optimizer

Usage: node optimize-build.js <command>

Commands:
  analyze  - Analyze current build bundle sizes
  test     - Run build performance test
  monitor  - Generate performance monitoring script
  deps     - Check for unused dependencies
  report   - Generate comprehensive optimization report

Examples:
  node optimize-build.js analyze
  node optimize-build.js test
  node optimize-build.js report
`);
     }
}

if (require.main === module) {
     main();
}

module.exports = BuildOptimizer;