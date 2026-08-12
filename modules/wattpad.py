import requests
from core.scrape import AVATAR_SKIP_MARKERS

class WattpadScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        try:
            r = requests.get(f"https://www.wattpad.com/api/v3/users/{username}/", timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if not isinstance(data, dict) or not data.get("username"):
                return False
            self.profile_url = f"https://www.wattpad.com/user/{data.get('username', username)}"
            if data.get("name"):
                self.meta["name"] = data["name"]
            avatar = data.get("avatar")
            if avatar and not any(m in avatar.lower() for m in AVATAR_SKIP_MARKERS):
                self.meta["avatar"] = avatar
            if data.get("description"):
                self.meta["bio"] = data["description"][:220]
            return True
        except: pass
        return False
