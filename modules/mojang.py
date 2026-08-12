import requests

class MojangScanner:
    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            uuid = data.get("id")
            if not uuid:
                return False
            self.profile_url = f"https://namemc.com/profile/{data.get('name', username)}"
            # Mojang's own API has no avatar field - crafatar renders one
            # straight from the account's skin, keyed by this same UUID, so
            # no extra lookup is needed to point at it.
            self.meta["avatar"] = f"https://crafatar.com/avatars/{uuid}?size=150&overlay"
            return True
        except: pass
        return False
