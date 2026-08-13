import os
import requests
from core.display import console
from dotenv import load_dotenv

load_dotenv()
KEYAPI_KEY = os.getenv("KEYAPI_KEY")


class InstagramScanner:
    """Extracts profile data from Instagram's public web_profile_info API.

    Prefers keyapi.ai's proxy of that same endpoint when KEYAPI_KEY is
    configured - more reliable than calling instagram.com directly, which
    frequently rate-limits or serves an HTML login wall to requests that
    look automated. Falls back to the direct call otherwise, so the module
    still works with no API key configured."""

    def __init__(self, username):
        self.username = username
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "x-ig-app-id": "936619743392459",
            "referer": "https://www.instagram.com/",
            "accept": "*/*",
        }

    def _fetch_via_keyapi(self):
        try:
            res = requests.get(
                "https://api.keyapi.ai/v1/instagram/web_profile_info",
                params={"username": self.username},
                headers={"Authorization": f"Bearer {KEYAPI_KEY}"},
                timeout=10,
            )
            if res.status_code != 200:
                return None
            data = res.json().get("data") or {}
        except Exception:
            return None
        # keyapi.ai's response shape wasn't confirmed to nest under "user"
        # the same way Instagram's own endpoint does - accept either.
        return data.get("user") or data or None

    def _fetch_direct(self):
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={self.username}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code != 200:
                return None
            data = res.json()
        except Exception:
            return None
        return (data.get("data") or {}).get("user")

    def scan(self):
        user = self._fetch_via_keyapi() if KEYAPI_KEY else None
        if not user:
            user = self._fetch_direct()
        if not user:
            return False

        console.module_header("INSTAGRAM")
        console.success("Instagram Profile", f"https://www.instagram.com/{self.username}/")

        full_name = user.get("full_name")
        if full_name:
            console.info("Full Name", full_name)

        bio = user.get("biography")
        if bio:
            console.info("Bio", bio)

        console.info("Verified", "Yes" if user.get("is_verified") else "No")
        console.info("Private Account", "Yes" if user.get("is_private") else "No")

        followers = (user.get("edge_followed_by") or {}).get("count")
        following = (user.get("edge_follow") or {}).get("count")
        posts = (user.get("edge_owner_to_timeline_media") or {}).get("count")
        stats = []
        if followers is not None: stats.append(f"{followers} followers")
        if following is not None: stats.append(f"{following} following")
        if posts is not None: stats.append(f"{posts} posts")
        if stats:
            console.info("Activity", " / ".join(stats))

        category = user.get("category_name") or user.get("business_category_name")
        if user.get("is_business_account") and category:
            console.info("Category", category)

        external_url = user.get("external_url")
        if external_url:
            console.info("Website", external_url)

        avatar = user.get("profile_pic_url_hd") or user.get("profile_pic_url")
        if avatar:
            console.info("", avatar)

        return True
