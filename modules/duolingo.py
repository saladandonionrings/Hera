import requests

class DuolingoScanner:
    def scan(self, email):
        url = f"https://www.duolingo.com/2017-06-30/users?email={email}"
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get("users"):
                return True
        except: pass
        return False