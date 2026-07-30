import os
import subprocess
import re
import requests
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from core.display import console

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/user.emails.read', 'https://www.googleapis.com/auth/directory.readonly']

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

def clean_ansi(text):
    return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)

class GoogleScanner:
    def __init__(self, target):
        self.target = target
        self.gaia_id = None
        self.creds = None
        self.client_config = None

        if GOOGLE_CLIENT_ID and GOOGLE_PROJECT_ID and GOOGLE_CLIENT_SECRET:
            self.client_config = {
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "project_id": GOOGLE_PROJECT_ID,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
        self._init_google_auth()

    def _init_google_auth(self):
        # Without OAuth credentials (GOOGLE_CLIENT_ID/PROJECT_ID/CLIENT_SECRET) we can't
        # fetch the profile photo via the People API, but the rest of the module (identity
        # via GHunt) still works — don't block the scan for this.
        if not self.client_config:
            return

        if os.path.exists('token.json'):
            try:
                self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            except Exception:
                self.creds = None

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception:
                    self.creds = self._run_oauth_flow()
            else:
                self.creds = self._run_oauth_flow()

            if self.creds:
                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())

    def _run_oauth_flow(self):
        """Lance le flow OAuth interactif"""
        try:
            flow = InstalledAppFlow.from_client_config(self.client_config, SCOPES)
            return flow.run_local_server(port=0, open_browser=False)
        except Exception as e:
            console.warning("Google Auth", f"Authentication impossible ({str(e)[:80]}). PFP not available")
            return None

    def fetch_photo(self):
        if not self.gaia_id or not self.creds: return
        try:
            service = build('people', 'v1', credentials=self.creds)
            person = service.people().get(resourceName=f'people/{self.gaia_id}', personFields='photos').execute()
            photos = person.get('photos', [])
            if photos:
                img_url = photos[0].get('url').replace('=s100', '=s500')
                console.success("Profile Photo", "Found (People API)")
                console.info("Photo URL", img_url)
        except Exception as e:
            pass

    def check_internal_status(self):
        """Vérifie le statut profond via batchexecute (OneID)"""
        url = "https://accounts.google.com/v3/signin/_/AccountsSignInUi/data/batchexecute?rpcids=Aho3hb,zKAP2e"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-Same-Domain": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        }
        payload = f'f.req=%5B%5B%5B%22Aho3hb%22%2C%22%5B%5C%22{self.target}%5C%22%5D%22%2Cnull%2C%221%22%5D%5D%5D'
        
        try:
            res = requests.post(url, data=payload, headers=headers, timeout=10)
            text = res.text

            if "identity-signin-deleted-account" in text or "zKAP2e" in text:
                alias_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                alias_info = f" (Internal Alias: {alias_match.group(0)})" if alias_match else ""
                console.success("Google Account", f"{console.RED}DELETED RECENTLY{console.RESET}{alias_info}")
                console.info("Status", "Recovery phase active (active < 20 days ago)")
                return True

            if "denied_by_policy" in text or "account_disabled" in text:
                console.failure("Google Account", "Account is DISABLED/BANNED.")
                return True
            
            if "identifierNotFound" in text or "IdpLookup" in text:
                console.failure("Google Account", "No account associated with this email.")
                return False

            return None
        except:
            return None

    def check_blogger(self):
        if not self.gaia_id: return
        url = f"https://www.blogger.com/profile/{self.gaia_id}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200 and "profile-name" in r.text:
                console.success("Blogger Profile", url)
        except: pass

    def scan(self):
        console.module_header("GOOGLE IDENTITY")
        
        try:
            process = subprocess.run(["ghunt", "email", self.target], capture_output=True, text=True)
            output = clean_ansi(process.stdout)

            name = re.search(r"🙋 (.*)", output)
            edit = re.search(r"Last profile edit : (.*)", output)
            gaia = re.search(r"Gaia ID : (.*)", output)
            
            if name: console.info("Profile Name", name.group(1).strip())
            if edit: console.info("Last Update", edit.group(1).strip())
            if gaia: 
                self.gaia_id = gaia.group(1).strip()
                console.info("Gaia ID", self.gaia_id)
                self.fetch_photo()

            u_types = re.search(r"User types :\n((?:- .*\n?)*)", output)
            if u_types: 
                types_list = u_types.group(1).strip().replace('- ', '').split('\n')
                console.info("User Types", ', '.join(types_list))

            svc_match = re.search(r"\[\+\] Activated Google services :\n((?:- .*\n?)*)", output)
            if svc_match:
                services = svc_match.group(1).strip().replace("- ", "").split("\n")
                console.info("Services", ', '.join(services))

            if not name and not gaia:
                self._report_ghunt_failure(process, output)

            self.check_blogger()

        except FileNotFoundError:
            console.error("GHunt", "`ghunt` not found (pip install ghunt).")
        except Exception as e:
            console.error("GHunt Error", str(e))

    def _report_ghunt_failure(self, process, output):
        """Donne une indication claire quand GHunt ne retourne aucune donnée exploitable,
        au lieu de laisser la section GOOGLE IDENTITY silencieusement vide."""
        stderr = clean_ansi(process.stderr or "").strip()
        combined = f"{output}\n{stderr}".lower()

        if "ghunt login" in combined or "not logged in" in combined or "cookies" in combined:
            console.warning("GHunt", "not authenticated - do `ghunt login`.")
        elif "does not exist" in combined or "no google account" in combined or "wasn't found" in combined or "was not found" in combined:
            console.failure("Google Account", "Not found.")
        elif "keyerror: 'container'" in combined:
            console.warning("GHunt", "Known Bug (KeyError 'container') — run `python3 scripts/patch_ghunt.py` to correct.")
        elif "keyerror" in combined or "traceback" in combined:
            console.warning("GHunt", "Internal error GHunt - try `pip install -U ghunt`.")
        elif process.returncode != 0:
            tail = (stderr or output).strip().splitlines()
            snippet = tail[-1][:100] if tail else f"code retour {process.returncode}"
            console.warning("GHunt", f"fail : ({snippet})")
        else:
            console.warning("GHunt", "no data.")