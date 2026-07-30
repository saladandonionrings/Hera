import requests

class HackerNewsScanner:
    def scan(self, username):
        url = f"https://hacker-news.firebaseio.com/v0/user/{username}.json"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and r.json() is not None:
                return True
        except: pass
        return False
