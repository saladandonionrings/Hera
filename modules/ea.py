from curl_cffi import requests
import re

class EAScanner:
    def __init__(self):
        self.url_init = "https://signin.ea.com/p/juno/resetPassword?execution=e1s1&initref=https%3A%2F%2Faccounts.ea.com%2Fconnect%2Fauth%3Fclient_id%3DEADOTCOM-WEB-SERVER"
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://signin.ea.com",
            "Referer": self.url_init
        }

    def scan(self, email):
        """
        Logic: 200 OK (Found) vs 302 Redirect (Not Found)
        """
        try:
            res_init = self.session.get(self.url_init, timeout=15)
            action_url = self.url_init 

            payload = {
                "email": email,
                "regionCode": "FR",
                "_eventId": "submit",
                "phoneNumber": "",
                "usingPhoneInput": "false"
            }

            response = self.session.post(
                action_url, 
                data=payload, 
                headers=self.headers, 
                timeout=15,
                allow_redirects=False 
            )

            if response.status_code == 200:
                return True
            
            elif response.status_code == 302:
                return False
                
            return None
        except Exception:
            return None