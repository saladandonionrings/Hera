import requests
from core.scrape import extract_profile_meta

class SmuleScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://www.smule.com/{username}"
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                self.profile_url = url
                self.meta = extract_profile_meta(r.text)
                return True
        except: pass
        return False
