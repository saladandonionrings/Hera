import requests
import re
from datetime import datetime
from core.display import console

class ProtonScanner:
    def __init__(self):
        self.headers = {
            "x-pm-appversion": "web-account@5.0.153.3",
            "x-pm-locale": "en_US",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def generate_auth_session(self):
        url = "https://account.proton.me/api/auth/v4/sessions"
        try:
            response = requests.post(url, headers=self.headers, timeout=10)
            data = response.json()
            return data['UID'], f"Bearer {data['AccessToken']}"
        except: return None, None

    def get_pgp_info(self, email):
        url = f"https://api.protonmail.ch/pks/lookup?op=index&search={email}"
        try:
            res = requests.get(url, timeout=10).text
            result = re.search(r'pub:[a-f0-9]+:(?:\d+):(?:\d+)?:(\d+)::', res)
            if result:
                timestamp = int(result.group(1))
                return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        except: pass
        return "Unknown"

    def scan(self, email):
        console.module_header("ProtonMail")
        
        uid, auth = self.generate_auth_session()
        if not uid:
            console.error("Proton API", "Failed to initialize session.")
            return

        self.headers["x-pm-uid"] = uid
        self.headers["Authorization"] = auth
        params = {"Name": email, "ParseDomain": "1"}
        url = "https://account.proton.me/api/core/v4/users/available"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 409:
                creation_date = self.get_pgp_info(email)
                console.info("Account created", creation_date)
                console.info("Public Key", f"https://api.protonmail.ch/pks/lookup?op=get&search={email}")
            elif '"Suggestions":[]' in response.text:
                console.failure("ProtonMail", "No account detected")
            else:
                console.warning("ProtonMail", "Uncertain status")
        except Exception as e:
            console.error("NeutrOSINT Error", str(e))