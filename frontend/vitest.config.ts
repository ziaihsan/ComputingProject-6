/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    // Environment - jsdom for browser-like testing
    environment: 'jsdom',

    // Global test APIs (describe, it, expect) without imports
    globals: true,

    // Setup file for global configurations
    setupFiles: ['./src/__tests__/setup.ts'],

    // Include test files
    include: ['src/**/*.{test,spec}.{ts,tsx}'],

    // Exclude patterns
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache'],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'text-summary', 'html'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'src/__tests__/',
        'src/main.tsx',
        '**/*.d.ts',
        '**/*.config.*',
        '**/types/**',
      ],
      // Coverage thresholds
      thresholds: {
        statements: 60,
        branches: 50,
        functions: 60,
        lines: 60,
      },
    },

    // Reporter - clean output
    reporters: ['default'],

    // Timeout for tests
    testTimeout: 10000,

    // CSS handling
    css: true,
  },
})
