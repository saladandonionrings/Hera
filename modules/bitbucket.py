import requests
from core.scrape import AVATAR_SKIP_MARKERS

class BitbucketScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://api.bitbucket.org/2.0/users/{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            self.profile_url = (data.get("links") or {}).get("html", {}).get("href") or f"https://bitbucket.org/{username}/"
            if data.get("display_name"):
                self.meta["name"] = data["display_name"]
            avatar = (data.get("links") or {}).get("avatar", {}).get("href")
            if avatar and not any(m in avatar.lower() for m in AVATAR_SKIP_MARKERS):
                self.meta["avatar"] = avatar
            if data.get("location"):
                self.meta["location"] = data["location"]
            if data.get("created_on"):
                self.meta["joined"] = data["created_on"].split("T")[0]
            return True
        except: pass
        return False
