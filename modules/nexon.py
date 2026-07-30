import uuid
from curl_cffi import requests

class NexonScanner:
    def __init__(self):
        self.url = "https://www.nexon.com/api/regional-auth/v1.0/no-auth/login/validate"
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://www.nexon.com",
            "Referer": "https://www.nexon.com/account/en/login",
            "X-Arena-Fe-Version": "account-v1.132.0-eaa30e2b",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    def scan(self, target):
        """
        Logic: 200 OK + Body vide = Succès (Compte trouvé).
        """
        device_id = str(uuid.uuid4())
        
        payload = {
            "id": target,
            "deviceId": device_id
        }

        try:
            response = self.session.post(
                self.url, 
                json=payload, 
                headers=self.headers, 
                timeout=15
            )

            if response.status_code == 200 and not response.content:
                return True
            
            return False
        except Exception:
            return None