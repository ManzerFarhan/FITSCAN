/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: "standalone", // small self-contained server for the Docker image
  distDir: process.env.NEXT_DIST_DIR || ".next", // lets a production build run beside `npm run dev`
  // Hosted (Vercel): set BACKEND_URL and NEXT_PUBLIC_API_BASE_URL=/api/v1. The browser then talks only to this
  // site, which forwards API calls to the backend - so login cookies are first-party and there is no CORS.
  async rewrites() {
    const backend = process.env.BACKEND_URL?.replace(/\/+$/, "");
    return backend ? [{ source: "/api/v1/:path*", destination: `${backend}/api/v1/:path*` }] : [];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(self)" },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
