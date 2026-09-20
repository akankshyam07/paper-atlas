/** @type {import('next').NextConfig} */
const nextConfig = {
  // ponytail: rewrite API calls to the FastAPI dev server. Point at prod later.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/:path*" },
    ];
  },
};
export default nextConfig;
