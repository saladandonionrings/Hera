import requests


class VintedScanner:
    """Vinted's user API (v2/users/{username}) requires a session cookie
    first obtained by visiting the main page - a bare API request without
    it gets rejected."""

    def __init__(self):
        self.profile_url = ""
        self.meta = {}

    def scan(self, username):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        })

        try:
            session.get("https://www.vinted.fr", timeout=10)
        except Exception:
            return False

        try:
            r = session.get(f"https://www.vinted.fr/api/v2/users/{username}", timeout=10)
            if r.status_code != 200:
                return False
            data = r.json()
        except Exception:
            return False

        user = data.get("user")
        if not user or not user.get("id"):
            return False

        self.profile_url = f"https://www.vinted.fr/member/{user['id']}"

        # Field names below are best-effort (Vinted's response shape wasn't
        # confirmed against a live example) - adjust if real output shows
        # different keys.
        avatar = (user.get("photo") or {}).get("url")
        if avatar:
            self.meta["avatar"] = avatar
        if user.get("real_name"):
            self.meta["name"] = user["real_name"]
        if user.get("about"):
            self.meta["bio"] = user["about"]

        location = ", ".join(p for p in [user.get("city"), user.get("country_title")] if p)
        if location:
            self.meta["location"] = location

        stats = []
        if user.get("item_count") is not None:
            stats.append(f"{user['item_count']} items")
        if user.get("followers_count") is not None:
            stats.append(f"{user['followers_count']} followers")
        if user.get("following_count") is not None:
            stats.append(f"{user['following_count']} following")
        if user.get("positive_feedback_count") is not None:
            stats.append(f"{user['positive_feedback_count']} positive reviews")
        if stats:
            self.meta["stats"] = " / ".join(stats)

        return True
