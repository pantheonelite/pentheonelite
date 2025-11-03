/** @type {import('next').NextConfig} */
const nextConfig = {
  // Leave output default (server) in dev to avoid static path requirements
  basePath: process.env.NEXT_PUBLIC_BASE_PATH,
};

export default nextConfig;
