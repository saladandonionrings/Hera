import requests

class GitLabScanner:
    def scan(self, username):
        url = f"https://gitlab.com/api/v4/users?username={username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and len(r.json()) > 0:
                return True
        except: pass
        return False
