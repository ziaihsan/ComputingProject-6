/**
 * MSW Server Setup
 *
 * Creates a mock server for Node.js environment (Vitest runs in Node).
 * This server intercepts HTTP requests and responds with mock data.
 */
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

// Create the mock server with all handlers
export const server = setupServer(...handlers)
