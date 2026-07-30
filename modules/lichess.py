import requests

class LichessScanner:
    def scan(self, username):
        url = f"https://lichess.org/api/user/{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.json().get("id"):
                return True
        except: pass
        return False
