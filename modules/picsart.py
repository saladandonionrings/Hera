import requests

class PicsartScanner:
    def scan(self, username):
        url = f"https://api.picsart.com/users/show/{username}.json"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if not isinstance(data, dict) or data.get("status") == "error":
                return False
            return True
        except: pass
        return False
