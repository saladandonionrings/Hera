import requests

class BitbucketScanner:
    def scan(self, username):
        url = f"https://api.bitbucket.org/2.0/users/{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return True
        except: pass
        return False
