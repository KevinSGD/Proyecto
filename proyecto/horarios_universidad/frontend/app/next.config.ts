import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: { unoptimized: true },
  // Removes the floating Next.js dev-tools "N" badge shown in dev mode.
  devIndicators: false,
}

export default nextConfig
