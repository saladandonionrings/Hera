import re
import requests
from core.display import console

class AcademiaScanner:
    def __init__(self):
        self.session = requests.Session()
        self.home_url = "https://www.academia.edu/"
        self.api_url = "https://www.academia.edu/v0/has_account?subdomain_param=api"
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.academia.edu",
            "referer": "https://www.academia.edu/",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }

    def _get_csrf_token(self):
        """Récupère le token CSRF depuis la page d'accueil."""
        try:
            response = self.session.get(self.home_url, headers=self.headers, timeout=10)
            match = re.search(r'<meta name="csrf-token" content="(.*?)"', response.text)
            if match:
                return match.group(1)
        except Exception as e:
            console.error("Academia CSRF", f"Error while retrieving token : {e}")
        return None

    def scan(self, email):
        csrf_token = self._get_csrf_token()
        
        if not csrf_token:
            return None

        self.headers["x-csrf-token"] = csrf_token
        
        payload = {"email": email}
        
        try:
            response = self.session.post(
                self.api_url, 
                json=payload, 
                headers=self.headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("has_account") is True:
                    first_name = data.get("first_name", "N/A")
                    return True
            return False
        except Exception:
            return None