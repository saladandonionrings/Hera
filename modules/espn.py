import os
import uuid
from curl_cffi import requests
from dotenv import load_dotenv

load_dotenv()

# Static Disney API key shared by all ESPN OneSite clients, not a personal
# credential — overridable via env var in case Disney rotates it.
DEFAULT_ESPN_API_KEY = "APIKEY xWZV1LqDkIGE/s3v7mAPnchxhOZ2dd6+69CuDjbG/vgz5cGon5GH7CYKmxmMQ3C7fwGASZivPesl7rVkQ+p85XxMBn+a"

class ESPNScanner:
    def __init__(self):
        self.url = "https://registerdisney.go.com/jgc/v8/client/ESPN-ONESITE.WEB-PROD/guest-flow?langPref=en-UK&feature=no-password-reuse"
        self.session = requests.Session(impersonate="chrome110")

        self.api_key = os.getenv("ESPN_API_KEY", DEFAULT_ESPN_API_KEY)
        
        self.headers = {
            "Accept": "*/*",
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Origin": "https://cdn.registerdisney.go.com",
            "Referer": "https://cdn.registerdisney.go.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

    def scan(self, email):
        """
        Logic: LOGIN_FLOW (exists) vs REGISTRATION_FLOW (not registrered)
        """
        conv_id = str(uuid.uuid4())
        corr_id = str(uuid.uuid4())
        
        self.headers["Conversation-Id"] = conv_id
        self.headers["Correlation-Id"] = corr_id
        
        payload = {"email": email}

        try:
            response = self.session.post(
                self.url, 
                json=payload, 
                headers=self.headers, 
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                flow = data.get("data", {}).get("guestFlow")

                if flow == "LOGIN_FLOW":
                    return True
                elif flow == "REGISTRATION_FLOW":
                    return False
            
            return None
        except Exception:
            return None