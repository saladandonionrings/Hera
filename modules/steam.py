import requests

class SteamScanner:
    def scan(self, username):
        url = f"https://steamid.uk/profile/{username}"
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        }
        try:
            r = requests.get(url, headers=headers, timeout=5, allow_redirects=False)
            location = r.headers.get("Location", "")
            if "/profile/7656" in location:
                return True
        except: pass
        return False