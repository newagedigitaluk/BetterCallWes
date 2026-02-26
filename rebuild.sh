#!/bin/bash
# Better Call Wes — Full Site Rebuild Script
# Run this after making any changes to the Python generators or content
# Usage: ./rebuild.sh

set -e

echo "🔧 Rebuilding Better Call Wes website..."
echo ""

echo "📄 Building Service Hub Pages..."
python3 build_hub_pages.py

echo "📄 Building Child Service Pages..."
python3 build_child_pages.py

echo "📍 Building Location Pages..."
python3 build_advanced_location_pages.py

echo "📋 Building Trust Pages (About, Contact, Pricing, Reviews)..."
python3 build_trust_pages.py

echo "🔍 Building Technical SEO files..."
python3 build_technical_seo.py

echo ""
echo "✅ All pages rebuilt successfully!"
echo ""
echo "To preview locally:  python3 -m http.server 8000 -d Website"
echo "To deploy:           git add . && git commit -m 'Update' && git push"
