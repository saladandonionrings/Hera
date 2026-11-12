import subprocess
import requests
import re
from core.display import console
from core.config import PROTON_DOMAINS 

def clean_ansi(text):
    return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)

class EmailSocialScanner:
    def __init__(self, target):
        self.target = target

    def check_bitmoji(self):
        url = "https://us-east-1-bitmoji.api.snapchat.com/api/user/find"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=utf-8",
            "Referer": "https://www.bitmoji.com/",
            "Origin": "https://www.bitmoji.com"
        }
        try:
            res = requests.post(url, headers=headers, json={"email": self.target}, timeout=10)
            if res.status_code == 200:
                print(f"  ✓  snapchat.com             Account Found via Bitmoji")
                return True
        except: pass
        return False

    def check_dealabs(self):
        url = "https://www.dealabs.com/graphql"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://www.dealabs.com",
            "Referer": "https://www.dealabs.com/",
        }
        query = """
            query userIdentity($identity: String!) {
              userIdentity(identity: $identity) {
                identityType
                isUserIdentified
              }
            }
        """
        payload = {"query": query, "variables": {"identity": self.target}}
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                user_identity = (res.json().get("data") or {}).get("userIdentity") or {}
                if user_identity.get("isUserIdentified"):
                    print(f"  ✓  dealabs.com              Account Found")
                    return True
        except: pass
        return False

    def check_notion(self):
        url = "https://app.notion.com/api/v3/getLoginOptions"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://app.notion.com",
            "Referer": "https://app.notion.com/login",
        }
        payload = {"email": self.target, "requireWorkTypeEmail": False}
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                if res.json().get("hasAccount"):
                    print(f"  ✓  notion.so                Account Found")
                    return True
        except: pass
        return False

    def scan(self, render_header=True):
        if render_header:
            console.module_header("EMAIL TO SOCIAL MEDIA")

        found = False
        is_proton_target = any(domain in self.target for domain in PROTON_DOMAINS)

        if self.check_bitmoji():
            found = True
        if self.check_dealabs():
            found = True
        if self.check_notion():
            found = True

        try:
            process = subprocess.run(["holehe", self.target, "--only-used"], capture_output=True, text=True)
            output = clean_ansi(process.stdout)
            lines = output.split('\n')
            
            for line in lines:
                if "[+]" in line and "Email used" not in line:
                    site_name = line.replace("[+]", "").strip()
                    site_name = site_name.split('(')[0].strip().lower()
                    
                    if is_proton_target and "proton" in site_name:
                        continue
                    
                    if "http" not in site_name:
                        print(f"  ✓  {site_name:<23} Account Found")
                        found = True
            
            if not found:
                console.failure("Social Networks", "No accounts detected")
        except Exception as e:
            console.error("Holehe CLI Error", str(e))