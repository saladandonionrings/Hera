import re
import requests
from core.scrape import extract_profile_meta

class SteamScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://steamid.uk/profile/{username}"
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        }
        try:
            r = requests.get(url, headers=headers, timeout=5, allow_redirects=False)
            location = r.headers.get("Location", "")
            match = re.search(r"(7656\d{13})", location)
            if not match:
                return False

            self.profile_url = f"https://steamcommunity.com/profiles/{match.group(1)}"
            try:
                profile_res = requests.get(self.profile_url, headers=headers, timeout=5)
                if profile_res.status_code == 200:
                    self.meta = extract_profile_meta(profile_res.text)
            except: pass

            return True
        except: pass
        return False
