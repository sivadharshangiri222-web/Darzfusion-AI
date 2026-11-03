#!/bin/bash
set -e

echo "=== Building DARZFUSION AI for Vercel ==="

# Create Vercel Build Output API v3 directories
mkdir -p .vercel/output/static

# Copy static assets into .vercel/output/static
cp index.html logo.png logo_full.jpg .vercel/output/static/

# Also copy into public for backwards compatibility
mkdir -p public
cp index.html logo.png logo_full.jpg public/

# Generate Vercel Build Output API v3 config
cat << 'EOF' > .vercel/output/config.json
{
  "version": 3,
  "routes": [
    { "handle": "filesystem" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
EOF

echo "=== Build completed successfully ==="
ls -la .vercel/output/static
