import requests

class NpmScanner:
    def scan(self, username):
        url = f"https://registry.npmjs.org/-/user/org.couchdb.user:{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return True
        except: pass
        return False
