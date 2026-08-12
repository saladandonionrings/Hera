import requests
from core.scrape import AVATAR_SKIP_MARKERS

class PicsartScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://api.picsart.com/users/show/{username}.json"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if not isinstance(data, dict) or data.get("status") == "error":
                return False
            self.profile_url = f"https://picsart.com/u/{username}"
            # Undocumented API - field names are a best guess, so every
            # lookup is defensive and simply contributes nothing if absent.
            name = data.get("full_name") or data.get("fullname") or data.get("name")
            if name:
                self.meta["name"] = name
            avatar = data.get("photo") or data.get("avatar") or data.get("profile_photo")
            if avatar and not any(m in str(avatar).lower() for m in AVATAR_SKIP_MARKERS):
                self.meta["avatar"] = avatar
            return True
        except: pass
        return False
