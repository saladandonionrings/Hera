import re
import datetime
import requests

class HackerNewsScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://hacker-news.firebaseio.com/v0/user/{username}.json"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if data is None:
                return False
            self.profile_url = f"https://news.ycombinator.com/user?id={username}"
            about = data.get("about")
            if about:
                self.meta["bio"] = re.sub(r"<[^>]+>", " ", about).strip()[:220]
            elif data.get("karma") is not None:
                self.meta["bio"] = f"{data['karma']} karma"
            if data.get("created"):
                self.meta["joined"] = datetime.datetime.utcfromtimestamp(data["created"]).strftime("%Y-%m-%d")
            return True
        except: pass
        return False
