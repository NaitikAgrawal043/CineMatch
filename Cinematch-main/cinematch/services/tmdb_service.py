import requests
import html
import urllib3
import os
import json
import subprocess
from django.conf import settings

# Disable SSL insecure warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
TMDB_BASE_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

# Pre-populated high-res poster paths for popular movies
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
    679: "/r1x5JG2Kv8refYKTn9MfW8MwBuJ.jpg",        # Aliens
    597: "/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",       # Titanic
    100402: "/k7e07aL6P0mXm0YV4K605Wf9e7h.jpg",   # Captain America: The Winter Soldier
    271110: "/x2LSRK2Cm7MZhjluni1msVJ3wDF.jpg",   # Captain America: Civil War
    1865: "/pE4s3E6VlDox0m0Lp7rG5hD5h2p.jpg",      # Pirates of the Caribbean
    11: "/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg",        # Star Wars
    299536: "/7WsyChvgzg9flRKiGe7A24qP8t4.jpg",    # Avengers Infinity War
    299534: "/or06FN3Dka5tukK1e9sl16pB3iy.jpg",    # Avengers Endgame
    8587: "/uxzzxijgPIY7slzFvMotPv8vlKA.jpg",       # The Lion King
    120: "/6oom5QYQ2yQTMJIbnvbkBL9cDK6.jpg",       # LOTR Fellowship
    121: "/5VTN0pR8gcqV3EPUHHfMGnJYN9L.jpg",       # LOTR Two Towers
    122: "/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg",       # LOTR Return of the King
    238: "/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",       # The Godfather
    278: "/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",       # Shawshank
    13: "/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg",         # Forrest Gump
}

# In-memory LRU cache for poster paths
_POSTER_PATH_CACHE = dict(CURATED_POSTER_PATHS)

def get_local_poster_dir():
    try:
        p_dir = os.path.join(settings.BASE_DIR, 'static', 'posters')
        os.makedirs(p_dir, exist_ok=True)
        return p_dir
    except:
        return None

def get_poster_path(movie_id):
    """Retrieve relative poster_path for a movie ID using DoH resolution."""
    if not movie_id:
        return None
    try:
        m_id = int(movie_id)
    except:
        return None

    if m_id in _POSTER_PATH_CACHE:
        return _POSTER_PATH_CACHE[m_id]
    
    # Check if we already have it cached on disk
    p_dir = get_local_poster_dir()
    if p_dir:
        disk_file = os.path.join(p_dir, f"{m_id}.jpg")
        if os.path.exists(disk_file) and os.path.getsize(disk_file) > 1000:
            return f"/local_{m_id}.jpg"

    # Query TMDB API with DNS-over-HTTPS (DoH) via curl to bypass ISP DNS poisoning
    try:
        api_url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_API_KEY}"
        cmd = ["curl.exe", "-s", "--connect-timeout", "3", "--doh-url", "https://1.1.1.1/dns-query", api_url]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
        if res.returncode == 0 and res.stdout:
            data = json.loads(res.stdout)
            path = data.get('poster_path')
            if path:
                _POSTER_PATH_CACHE[m_id] = path
                return path
    except Exception as e:
        print(f"[TMDBService] DoH Lookup error for {m_id}: {e}")

    return None

def fetch_poster_binary(poster_path, movie_id=None):
    """Fetch raw binary image data from local disk or TMDB CDN."""
    p_dir = get_local_poster_dir()

    # 1. Check local disk cache first by movie_id
    if movie_id and p_dir:
        try:
            m_id = int(movie_id)
            disk_file = os.path.join(p_dir, f"{m_id}.jpg")
            if os.path.exists(disk_file) and os.path.getsize(disk_file) > 1000:
                with open(disk_file, 'rb') as f:
                    return f.read(), 'image/jpeg'
        except:
            pass

    if not poster_path:
        return None, None
    
    # 2. Check if path indicates local file
    if poster_path.startswith('/local_') and p_dir:
        filename = poster_path[7:]
        disk_file = os.path.join(p_dir, filename)
        if os.path.exists(disk_file) and os.path.getsize(disk_file) > 1000:
            with open(disk_file, 'rb') as f:
                return f.read(), 'image/jpeg'

    # 3. Fetch from TMDB CDN (image.tmdb.org) using DoH via curl to bypass ISP DNS poisoning
    clean_path = poster_path if poster_path.startswith('/') else f"/{poster_path}"
    full_url = f"{TMDB_BASE_IMAGE_URL}{clean_path}"

    doh_servers = ["https://1.1.1.1/dns-query", "https://9.9.9.9/dns-query"]
    for doh_url in doh_servers:
        try:
            cmd = [
                "curl.exe", "-s", "-L",
                "--connect-timeout", "6",
                "--max-time", "10",
                "--doh-url", doh_url,
                "-k",  # ignore SSL errors (same as verify=False)
                "-A", HEADERS['User-Agent'],
                "-o", "-",  # output to stdout
                full_url
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=12)
            if result.returncode == 0 and len(result.stdout) > 1000:
                # Check it's a real image (JPEG magic bytes: FF D8, PNG: 89 50, WEBP: 52 49)
                header = result.stdout[:4]
                if header[:2] == b'\xff\xd8':
                    content_type = 'image/jpeg'
                elif header[:4] == b'\x89PNG':
                    content_type = 'image/png'
                elif header[:4] == b'RIFF':
                    content_type = 'image/webp'
                else:
                    # Not a valid image — likely an error page
                    print(f"[TMDBService] Non-image response for {poster_path} via {doh_url}")
                    continue

                # Save to disk cache for future instant loads
                if movie_id and p_dir:
                    try:
                        disk_file = os.path.join(p_dir, f"{int(movie_id)}.jpg")
                        with open(disk_file, 'wb') as f:
                            f.write(result.stdout)
                    except:
                        pass

                return result.stdout, content_type
        except Exception as e:
            print(f"[TMDBService] CDN curl fetch error for {poster_path} via {doh_url}: {e}")

    # Fallback: try with requests (in case curl is not available)
    try:
        resp = requests.get(full_url, headers=HEADERS, verify=False, timeout=8.0)
        if resp.status_code == 200 and 'image' in resp.headers.get('Content-Type', ''):
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
            if movie_id and p_dir:
                try:
                    disk_file = os.path.join(p_dir, f"{int(movie_id)}.jpg")
                    with open(disk_file, 'wb') as f:
                        f.write(resp.content)
                except:
                    pass
            return resp.content, content_type
    except Exception as e:
        print(f"[TMDBService] requests fallback fetch note for {poster_path}: {e}")

    return None, None

def generate_fallback_svg(title="Movie Poster", movie_id=None):
    """
    Dynamically generates a stylized Cinema SVG Poster.
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
        text_elements += f'<text x="150" y="{y_pos}" text-anchor="middle" font-family="Inter, Segoe UI, sans-serif" font-size="19" font-weight="700" fill="#b45309">{line}</text>\n'

    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" width="300" height="450">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fffbeb"/>
      <stop offset="50%" stop-color="#fef3c7"/>
      <stop offset="100%" stop-color="#fef08a"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="300" height="450" rx="14" fill="url(#bgGrad)"/>
  
  <!-- Outer Borders -->
  <rect x="10" y="10" width="280" height="430" rx="10" fill="none" stroke="#fcd34d" stroke-width="2"/>
  <rect x="18" y="18" width="264" height="414" rx="8" fill="none" stroke="#fde68a" stroke-width="1"/>

  <!-- Sprocket Holes -->
  <rect x="12" y="30" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="70" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="110" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="150" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="190" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="230" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="270" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="310" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="350" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="12" y="390" width="8" height="12" rx="2" fill="#d97706"/>

  <rect x="280" y="30" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="70" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="110" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="150" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="190" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="230" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="270" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="310" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="350" width="8" height="12" rx="2" fill="#d97706"/>
  <rect x="280" y="390" width="8" height="12" rx="2" fill="#d97706"/>

  <!-- Film Reel Centerpiece -->
  <g transform="translate(150, 135)">
    <circle cx="0" cy="0" r="48" fill="#fef3c7" stroke="#f59e0b" stroke-width="2"/>
    <circle cx="0" cy="0" r="38" fill="#ffffff" stroke="#fde68a" stroke-width="1.5"/>
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
  <text x="150" y="231" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#b45309" letter-spacing="2">CINEMATCH</text>

  <!-- Title Text -->
  {text_elements}

  <!-- Footnote -->
  <text x="150" y="415" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="#b45309">Cinema Showcase Poster</text>
</svg>'''
    return svg_content
