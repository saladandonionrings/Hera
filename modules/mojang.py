import requests

class MojangScanner:
    def scan(self, username):
        url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.json().get("id"):
                return True
        except: pass
        return False
