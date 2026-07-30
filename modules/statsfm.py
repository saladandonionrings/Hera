import requests

class StatsfmScanner:
    def scan(self, username):
        url = f"https://stats.fm/{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return True
        except: pass
        return False