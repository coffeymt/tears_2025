/// <reference types="vitest" />
import '@testing-library/jest-dom'
import { server } from './test/msw/server'

// Start MSW before all tests and close after
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
