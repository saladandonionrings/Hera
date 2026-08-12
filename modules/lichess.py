import requests

class LichessScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://lichess.org/api/user/{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if not data.get("id"):
                return False
            self.profile_url = data.get("url") or f"https://lichess.org/@/{username}"
            profile = data.get("profile") or {}
            full_name = " ".join(p for p in [profile.get("firstName"), profile.get("lastName")] if p)
            if full_name:
                self.meta["name"] = full_name
            if profile.get("bio"):
                self.meta["bio"] = profile["bio"][:220]
            if profile.get("country"):
                self.meta["location"] = profile["country"]
            return True
        except: pass
        return False
