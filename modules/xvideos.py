import requests

class XvideosScanner:
    def scan(self, email):
        url = f"https://www.xvideos.com/account/checkemail?email={email}"
        try:
            r = requests.get(url, timeout=5)
            if r.json().get("available") == False:
                return True
        except: pass
        return False