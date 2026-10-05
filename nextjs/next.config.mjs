/** @type {import('next').NextConfig} */

// The browser calls the API directly at NEXT_PUBLIC_API_URL (http://localhost:8000), so no proxy is needed.
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
