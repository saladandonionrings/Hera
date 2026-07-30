import requests
from core.display import console

class SpotifyScanner:
    def scan(self, email):
        url = f"https://spclient.wg.spotify.com/signup/public/v1/check-email?email={email}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.json().get("status") == 20:
                return True
        except: pass
        return False