import requests

class TwitterScanner:
    def scan(self, email):
        url = f"https://api.twitter.com/i/users/email_available.json?email={email}"
        try:
            r = requests.get(url, timeout=5)
            if r.json().get("taken") == True:
                return True
        except: pass
        return False