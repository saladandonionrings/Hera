import requests

class SmuleScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://www.smule.com/api/profile/?handle={username}"
        headers = {
            "accept": "application/json, text/plain, */*",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "referer": f"https://www.smule.com/{username}",
        }
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code != 200:
                return False
            data = r.json()
        except Exception:
            return False

        # A missing handle doesn't return a real account_id - the profile
        # page itself (the old check target) returned 200 regardless of
        # whether the handle existed, causing false positives.
        if not data.get("account_id"):
            return False

        self.profile_url = f"https://www.smule.com/{username}"

        if data.get("pic_url"):
            self.meta["avatar"] = data["pic_url"]
        if data.get("blurb"):
            self.meta["bio"] = data["blurb"]
        if data.get("location"):
            self.meta["location"] = data["location"]

        stats = []
        if data.get("followers") is not None:
            stats.append(f"{data['followers']} followers")
        if data.get("followees") is not None:
            stats.append(f"{data['followees']} following")
        if data.get("num_performances") is not None:
            stats.append(f"{data['num_performances']} performances")
        if stats:
            self.meta["stats"] = " / ".join(stats)

        return True
