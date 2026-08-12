import requests
from core.scrape import AVATAR_SKIP_MARKERS

class GitLabScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://gitlab.com/api/v4/users?username={username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if not data:
                return False
            user = data[0]
            self.profile_url = user.get("web_url") or f"https://gitlab.com/{username}"
            if user.get("name"):
                self.meta["name"] = user["name"]
            avatar = user.get("avatar_url")
            if avatar and not any(m in avatar.lower() for m in AVATAR_SKIP_MARKERS):
                self.meta["avatar"] = avatar
            return True
        except: pass
        return False
