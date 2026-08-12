import requests

class NpmScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://registry.npmjs.org/-/user/org.couchdb.user:{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            self.profile_url = f"https://www.npmjs.com/~{username}"
            if isinstance(data, dict) and data.get("fullname"):
                self.meta["name"] = data["fullname"]
            return True
        except: pass
        return False
