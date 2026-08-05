import requests

class WattpadScanner:
    def __init__(self):
        self.profile_url = ""

    def scan(self, username):
        try:
            r = requests.get(f"https://www.wattpad.com/api/v3/users/{username}/", timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if not isinstance(data, dict) or not data.get("username"):
                return False
            self.profile_url = f"https://www.wattpad.com/user/{data.get('username', username)}"
            return True
        except: pass
        return False
