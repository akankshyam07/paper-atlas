/** @type {import('next').NextConfig} */
const nextConfig = {
  // A production build and `next dev` share .next and overwrite each other's
  // chunks, which leaves the dev server throwing "Cannot find module './xxx.js'".
  // Verification builds write elsewhere via BUILD_DIR.
  distDir: process.env.BUILD_DIR || ".next",
  // ponytail: rewrite API calls to the FastAPI dev server. Point at prod later.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/:path*" },
    ];
  },
};
export default nextConfig;
