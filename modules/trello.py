import requests

class TrelloScanner:
    def __init__(self):
        self.profile_url = ""

    def scan(self, username):
        try:
            r = requests.get(f"https://trello.com/1/members/{username}", timeout=5)
            if r.status_code != 200:
                return False
            data = r.json()
            if not isinstance(data, dict) or not data.get("id"):
                return False
            self.profile_url = f"https://trello.com/{data.get('username', username)}"
            return True
        except: pass
        return False
