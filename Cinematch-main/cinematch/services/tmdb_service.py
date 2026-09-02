import requests
import html
import urllib3
from functools import lru_cache

# Disable SSL insecure warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
TMDB_BASE_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

# Pre-populated high-res poster paths for popular and benchmark movies
CURATED_POSTER_PATHS = {
    155: "/qJ2tW6WMUDux911r6m7haRef0WH.jpg",      # The Dark Knight
    27205: "/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg",    # Inception
    19995: "/kyeqWdyUXW608qlYkRqosgbbJyK.jpg",    # Avatar
    157336: "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",   # Interstellar
    24428: "/RYMX2wcKCBAr24UyPD7xwmjaTn.jpg",     # The Avengers
    680: "/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg",       # Pulp Fiction
    550: "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",       # Fight Club
    603: "/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",       # The Matrix
    1726: "/78lPtwv72eTNqFW9COBYI0dWDJa.jpg",      # Iron Man
    679: "/r1x5JG2Kv8refYKTn9MfW8MwBuJ.jpg",       # Aliens
    597: "/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",       # Titanic
    100402: "/k7e07aL6P0mXm0YV4K605Wf9e7h.jpg",   # Captain America: The Winter Soldier
    271110: "/x2LSRK2Cm7MZhjluni1msVJ3wDF.jpg",   # Captain America: Civil War
    1865: "/pE4s3E6VlDox0m0Lp7rG5hD5h2p.jpg",      # Pirates of the Caribbean
    11: "/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg",        # Star Wars
}

# In-memory LRU cache for poster paths
_POSTER_PATH_CACHE = dict(CURATED_POSTER_PATHS)

def get_poster_path(movie_id):
    """Retrieve relative poster_path for a movie ID with local in-memory caching."""
    if not movie_id:
        return None
    try:
        m_id = int(movie_id)
    except:
        return None

    if m_id in _POSTER_PATH_CACHE:
        return _POSTER_PATH_CACHE[m_id]
    
    try:
        url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_API_KEY}&language=en-US"
        resp = requests.get(url, headers=HEADERS, verify=False, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            path = data.get('poster_path')
            if path:
                _POSTER_PATH_CACHE[m_id] = path
                return path
    except Exception as e:
        print(f"[TMDBService] API lookup note for movie {m_id}: {e}")
    
    return None

def fetch_poster_binary(poster_path):
    """Fetch raw binary image data from TMDB CDN with verify=False."""
    if not poster_path:
        return None, None
    
    clean_path = poster_path if poster_path.startswith('/') else f"/{poster_path}"
    full_url = f"{TMDB_BASE_IMAGE_URL}{clean_path}"
    try:
        resp = requests.get(full_url, headers=HEADERS, verify=False, timeout=3.5)
        if resp.status_code == 200 and 'image' in resp.headers.get('Content-Type', ''):
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
            return resp.content, content_type
    except Exception as e:
        print(f"[TMDBService] CDN fetch note for {poster_path}: {e}")
    
    return None, None

def generate_fallback_svg(title="Movie Poster", movie_id=None):
    """
    Dynamically generates a stylized Cinema SVG Poster complete with:
    - Light/Dark themed Cinema Card
    - Film strip perforations & reel graphics
    - Movie title typography
    """
    safe_title = html.escape(title or "Cinema Movie")
    
    words = safe_title.split()
    lines = []
    curr = []
    for w in words:
        if len(" ".join(curr + [w])) <= 16:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    
    lines = lines[:3]
    text_elements = ""
    start_y = 290 - (len(lines) - 1) * 15
    for idx, line in enumerate(lines):
        y_pos = start_y + (idx * 28)
        text_elements += f'<text x="150" y="{y_pos}" text-anchor="middle" font-family="Outfit, Segoe UI, sans-serif" font-size="19" font-weight="700" fill="#d97706">{line}</text>\n'

    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" width="300" height="450">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="50%" stop-color="#f8fafc"/>
      <stop offset="100%" stop-color="#f1f5f9"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="300" height="450" rx="14" fill="url(#bgGrad)"/>
  
  <!-- Outer Borders -->
  <rect x="10" y="10" width="280" height="430" rx="10" fill="none" stroke="#fcd34d" stroke-width="2"/>
  <rect x="18" y="18" width="264" height="414" rx="8" fill="none" stroke="#e2e8f0" stroke-width="1"/>

  <!-- Sprocket Holes -->
  <rect x="12" y="30" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="70" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="110" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="150" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="190" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="230" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="270" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="310" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="350" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="12" y="390" width="8" height="12" rx="2" fill="#cbd5e1"/>

  <rect x="280" y="30" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="70" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="110" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="150" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="190" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="230" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="270" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="310" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="350" width="8" height="12" rx="2" fill="#cbd5e1"/>
  <rect x="280" y="390" width="8" height="12" rx="2" fill="#cbd5e1"/>

  <!-- Film Reel Centerpiece -->
  <g transform="translate(150, 135)">
    <circle cx="0" cy="0" r="48" fill="#fef3c7" stroke="#f59e0b" stroke-width="2"/>
    <circle cx="0" cy="0" r="38" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5"/>
    <circle cx="0" cy="0" r="14" fill="#f59e0b"/>
    <circle cx="0" cy="-22" r="6" fill="#fef3c7" stroke="#d97706" stroke-width="1"/>
    <circle cx="19" cy="-11" r="6" fill="#fef3c7" stroke="#d97706" stroke-width="1"/>
    <circle cx="19" cy="11" r="6" fill="#fef3c7" stroke="#d97706" stroke-width="1"/>
    <circle cx="0" cy="22" r="6" fill="#fef3c7" stroke="#d97706" stroke-width="1"/>
    <circle cx="-19" cy="11" r="6" fill="#fef3c7" stroke="#d97706" stroke-width="1"/>
    <circle cx="-19" cy="-11" r="6" fill="#fef3c7" stroke="#d97706" stroke-width="1"/>
  </g>

  <!-- Cinema Badge -->
  <rect x="90" y="215" width="120" height="24" rx="12" fill="#fef3c7" stroke="#fde68a" stroke-width="1"/>
  <text x="150" y="231" text-anchor="middle" font-family="Outfit, sans-serif" font-size="11" font-weight="700" fill="#b45309" letter-spacing="2">CINEMATCH</text>

  <!-- Title Text -->
  {text_elements}

  <!-- Footnote -->
  <text x="150" y="415" text-anchor="middle" font-family="Outfit, sans-serif" font-size="10" fill="#94a3b8">Cinema Showcase Poster</text>
</svg>'''
    return svg_content
