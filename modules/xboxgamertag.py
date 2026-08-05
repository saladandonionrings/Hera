import requests

class XboxGamertagScanner:
    def scan(self, username):
        url = f"https://xboxgamertag.com/search/{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return True
        except: pass
        return False
