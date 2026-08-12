import requests

class RobloxScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

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
            user = data[0]
            user_id = user.get("id")
            if user_id:
                self.profile_url = f"https://www.roblox.com/users/{user_id}/profile"
            if user.get("displayName") and user["displayName"] != user.get("name"):
                self.meta["name"] = user["displayName"]

            if user_id:
                try:
                    thumb = requests.get(
                        "https://thumbnails.roblox.com/v1/users/avatar-headshot",
                        params={"userIds": user_id, "size": "150x150", "format": "png", "isCircular": "false"},
                        timeout=5,
                    )
                    if thumb.status_code == 200:
                        entries = thumb.json().get("data", [])
                        if entries and entries[0].get("state") == "Completed":
                            self.meta["avatar"] = entries[0].get("imageUrl")
                except: pass

            return True
        except: pass
        return False
