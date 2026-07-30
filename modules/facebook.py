import os
import requests
import json
from dotenv import load_dotenv
from core.display import console

load_dotenv()

# Static LSD token used to query Facebook's anonymous account-search API. Not
# a personal credential (not tied to any account) — overridable via env var
# in case Facebook rotates it.
DEFAULT_LSD_TOKEN = "AdTRP68PUkiTcszHBRwHQAbrFWU"

class FacebookScanner:
    def __init__(self, email):
        self.email = email
        self.url = 'https://www.facebook.com/api/graphql/'

    def scan(self, render_header=True):
        if render_header:
            console.module_header("FACEBOOK")

        lsd_token = os.getenv("FACEBOOK_LSD_TOKEN", DEFAULT_LSD_TOKEN)
        
        payload = {
            'lsd': lsd_token,
            'jazoest': '22329',
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'CAAFBAccountSearchViewQuery',
            'variables': json.dumps({
                "params": {
                    "search_query": self.email,
                    "context": "recover",
                    "friend_name": ""
                }
            }),
            'doc_id': '25765860633071922',
            '__a': '1',
            '__user': '0'
        }

        headers = {
            'authority': 'www.facebook.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.facebook.com',
            'referer': 'https://www.facebook.com/login/identify/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'x-fb-lsd': lsd_token,
            'x-asbd-id': '129477'
        }

        try:
            session = requests.Session()
            response = session.post(self.url, data=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except:
                    json_str = response.text.split('for (;;);')[-1]
                    data = json.loads(json_str)

                search_results = data.get('data', {}).get('account_search', {}).get('account_results', [])
                
                if search_results:
                    user = search_results[0]
                    console.success("Facebook", "Account Found")
                    console.info("Display Name", user.get('name', 'N/A'))
                    console.info("Profile ID", user.get('id', 'N/A'))
                    
                    pic = user.get('profile_picture', {}).get('uri')
                    if pic:
                        console.sub_item("Profile Pic", pic)
                    
                    mask = user.get('phone_number_mask')
                    if mask:
                        console.info("Phone Mask", mask)
                    return True
                if not search_results:
                    pass
            else:
                console.error("Facebook API", f"Error {response.status_code} (Request Rejected)")
                
        except Exception as e:
            console.error("Facebook Scanner", f"Fail: {str(e)[:50]}")
            
        return False