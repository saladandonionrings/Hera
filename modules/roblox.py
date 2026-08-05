import requests

class RobloxScanner:
    def __init__(self):
        self.profile_url = ""

    def scan(self, username):
        try:
            r = requests.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [username], "excludeBannedUsers": False},
                timeout=5,
            )
            if r.status_code != 200:
                return False
            data = r.json().get("data", [])
            if not data:
                return False
            user_id = data[0].get("id")
            if user_id:
                self.profile_url = f"https://www.roblox.com/users/{user_id}/profile"
            return True
        except: pass
        return False
