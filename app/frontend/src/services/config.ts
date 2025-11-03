// API Base URL Configuration
// In production (pantheonelite.ai), requests go to api.pantheonelite.ai
// In development, defaults to localhost
const getApiBaseUrl = () => {
  // Check if we're in production (pantheonelite.ai domain)
  if (typeof window !== 'undefined' && window.location.hostname === 'pantheonelite.ai') {
    return 'https://api.pantheonelite.ai';
  }
  // Use Next.js client env var or default to localhost for development
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE_URL;
  return fromEnv && fromEnv.length > 0 ? fromEnv : 'http://localhost:8000';
};

export const API_BASE_URL = getApiBaseUrl();
