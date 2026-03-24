import re

file_path = '/home/antigravity/Projects/Better Call Wes/Website/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

schema_script = '''    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "LocalBusiness",
      "name": "Better Call Wes",
      "image": "https://bettercallwes.co.uk/assets/logo.png?v=3",
      "@id": "https://bettercallwes.co.uk/",
      "url": "https://bettercallwes.co.uk/",
      "telephone": "07700155655",
      "address": {
        "@type": "PostalAddress",
        "addressLocality": "Southampton",
        "addressRegion": "Hampshire",
        "addressCountry": "UK"
      },
      "geo": {
        "@type": "GeoCoordinates",
        "latitude": 50.9097,
        "longitude": -1.4044
      },
      "openingHoursSpecification": {
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": [
          "Monday",
          "Tuesday",
          "Wednesday",
          "Thursday",
          "Friday"
        ],
        "opens": "08:00",
        "closes": "18:00"
      },
      "sameAs": [
        "https://www.facebook.com/bettercallwes",
        "https://www.instagram.com/bettercallwes"
      ]
    }
    </script>
'''

# Check if application/ld+json is already there
if 'application/ld+json' not in content:
    new_content = re.sub(r'</head>', schema_script + '</head>', content, count=1, flags=re.IGNORECASE)
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Schema added successfully.')
    else:
        print('Failed to add schema.')
else:
    print('Schema already exists.')
