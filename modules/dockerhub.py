import requests
from core.scrape import AVATAR_SKIP_MARKERS

class DockerHubScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://hub.docker.com/v2/users/{username}/"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            self.profile_url = f"https://hub.docker.com/u/{username}"
            if data.get("full_name"):
                self.meta["name"] = data["full_name"]
            avatar = data.get("gravatar_url")
            if avatar and not any(m in avatar.lower() for m in AVATAR_SKIP_MARKERS):
                self.meta["avatar"] = avatar
            location = ", ".join(p for p in [data.get("location"), data.get("company")] if p)
            if location:
                self.meta["location"] = location
            if data.get("date_joined"):
                self.meta["joined"] = data["date_joined"].split("T")[0]
            return True
        except: pass
        return False
