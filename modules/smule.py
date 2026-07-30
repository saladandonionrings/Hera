import requests

class SmuleScanner:
    def scan(self, username):
        url = f"https://www.smule.com/{username}"
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                return True
        except: pass
        return False
