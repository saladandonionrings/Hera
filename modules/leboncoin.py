from curl_cffi import requests
import random
import time

class LeboncoinScanner:
    def __init__(self):
        self.url_home = "https://www.leboncoin.fr/"
        self.url_auth = "https://auth.leboncoin.fr/api/authenticator/v1/users/pre_login"
        self.session = requests.Session(impersonate="chrome110")
        
        self.headers = {
            "Accept": "application/json",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://auth.leboncoin.fr",
            "Referer": "https://auth.leboncoin.fr/login/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Connection": "keep-alive"
        }

    def _init_session(self):
        """Visite la home pour choper les cookies DataDome frais"""
        try:
            h = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
            self.session.get(self.url_home, headers=h, timeout=10)
            time.sleep(random.uniform(1, 2))
            return True
        except:
            return False

    def scan(self, email):
        """Vérifie l'existence d'un compte LBC"""
        if not self.session.cookies:
            self._init_session()

        payload = {
            "email": email,
            "client_id": "lbc-front-web",
            "redirect_uri": "https://auth.leboncoin.fr/api/authorizer/v2/authorize?client_id=lbc-front-web&redirect_uri=https%3A%2F%2Fwww.leboncoin.fr%2Foauth2callback&response_type=code&scope=%2A+offline&state=82f34ed4-0e36-47b1-be42-d60912b4dd54",
            "from_to": "https://www.leboncoin.fr/"
        }

        try:
            response = self.session.post(
                self.url_auth, 
                json=payload, 
                headers=self.headers, 
                timeout=15
            )

            if response.status_code == 403:
                return None
                
            data = response.json()
            status = data.get("pre_login_status")

            if status == "PASSWORD_REQUIRED":
                return True
            elif status == "NO_ACCOUNT":
                return False
            
            return None
        except Exception:
            return None