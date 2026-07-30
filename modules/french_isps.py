import requests

class ISPScanner:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'idme',
            'Origin': 'https://login.orange.fr',
            'Referer': 'https://login.orange.fr/'
        }

    def check_orange(self, email):
        url = 'https://login.orange.fr/api/login'
        data = {"login": email, "loginOrigin": "input"}
        try:
            r = requests.post(url, json=data, headers=self.headers, timeout=10)
            if r.status_code != 401:
                return False
            return True
        except:
            return False

    def check_sfr(self, email):
        url = "https://espace-client.sfr.fr/gestion-securite/mot-de-passe/oublie/verification"
        try:
            r = requests.post(url, data={"identifier": email}, timeout=5)
            if "reinitialiser" in r.text.lower():
                return True
        except: pass
        return False

    def check_mycanal(self, email):
        url = "https://pass.canalplus.com/api/v1/check-email"
        try:
            r = requests.post(url, json={"email": email}, timeout=5)
            if r.json().get("exists") == True:
                return True
        except: pass
        return False