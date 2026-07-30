import hashlib
import requests
from core.display import console

class WordPressEmailScanner:
    def __init__(self, email):
        self.email = email.lower().strip()

    def scan(self, silent_if_not_found=False):
        email_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        url = f"https://en.gravatar.com/{email_hash}.json"
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                payload = response.json()
                entries = payload.get("entry", [])
                if not entries:
                    if not silent_if_not_found:
                        console.failure("Gravatar", "No profile found.")
                    return None

                data = entries[0]

                if silent_if_not_found:
                    console.module_header("WordPress / Gravatar")

                username = data.get("preferredUsername")
                display_name = data.get("displayName")
                
                console.info("WordPress username", f"@{username}")
                console.info("Display name", display_name)
                console.info("URL", url)
                
                if data.get("aboutMe"):
                    console.info("Bio", data.get("aboutMe").strip())
                
                accounts = data.get("accounts", [])
                if accounts:
                    console.info("Connected Services", f"Found {len(accounts)} links")
                    for acc in accounts:
                        console.sub_item(acc.get('shortname', '?').capitalize(), acc.get('url'))
                
                return username
            
            elif not silent_if_not_found:
                console.failure("Gravatar", "No profile found.")
                
        except Exception as e:
            if not silent_if_not_found:
                console.error("WordPress", f"Error: {e}")
        
        return None