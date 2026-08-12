import requests
from core.scrape import AVATAR_SKIP_MARKERS

class TrelloScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        try:
            r = requests.get(f"https://trello.com/1/members/{username}", timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if not isinstance(data, dict) or not data.get("id"):
                return False
            self.profile_url = f"https://trello.com/{data.get('username', username)}"
            if data.get("fullName"):
                self.meta["name"] = data["fullName"]
            avatar = data.get("avatarUrl")
            if avatar and not any(m in avatar.lower() for m in AVATAR_SKIP_MARKERS):
                self.meta["avatar"] = f"{avatar}/170.png"
            if data.get("bio"):
                self.meta["bio"] = data["bio"][:220]
            return True
        except: pass
        return False
