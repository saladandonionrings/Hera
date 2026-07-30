import re
from curl_cffi import requests
from core.display import console

class VivinoScanner:
    def __init__(self):
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.vivino.com/FR/fr/",
        }

    def scan(self, email):
        alias = email.split('@')[0] if "@" in email else email
        url = f"https://www.vivino.com/users/{alias}"
        
        try:
            res = self.session.get(url, headers=self.headers, timeout=15)
            
            if res.status_code == 200:
                html = res.text
                is_generic = any(x in html for x in ["Explore wines", "Shop the world", "Search results"])
                
                has_user_id = '"user_id":' in html or 'user_id=' in html
                
                og_title = re.search(r'property="og:title" content="(.*?)"', html)
                is_real_profile = og_title and "sur Vivino" in og_title.group(1)

                if not is_generic and has_user_id and is_real_profile:
                    console.module_header("VIVINO")
                    self._parse_profile(url, html)
                    return True
            
            return False
        except Exception as e:
            console.error("Vivino Error", str(e))
            return None

    def _parse_profile(self, url, html):
        console.success("vivino.com", "Account Found")
        console.info("Profile", url)

        name = re.search(r'<title>(.*?) sur Vivino', html)
        if name:
            clean_name = name.group(1).replace(" sur Vivino", "").strip()
            if clean_name.lower() != "wine":
                console.info("Name", clean_name)

        user_id = re.search(r'user_id=(\d+)', html)
        if not user_id:
            user_id = re.search(r'"user_id":(\d+)', html)

        if user_id:
            console.info("User ID", user_id.group(1))

        location = re.search(r'"country_code":"(.*?)"', html)
        if location:
            console.info("Location", location.group(1).upper())

        followers = re.search(r'"followers_count":(\d+)', html)
        ratings = re.search(r'"ratings_count":(\d+)', html)

        if not followers:
            followers = re.search(r'(\d+)\s+followers', html, re.IGNORECASE)

        stats = []
        if followers: stats.append(f"{followers.group(1)} followers")
        if ratings: stats.append(f"{ratings.group(1)} ratings")

        if stats:
            console.info("Activity", ' / '.join(stats))

        image = re.search(r'property="og:image" content="(.*?)"', html)
        if image and "default_user" not in image.group(1):
            console.info("Avatar", image.group(1))