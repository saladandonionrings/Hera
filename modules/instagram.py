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
        """Returns (user_dict_or_None, error_reason_or_None) - unlike a bare
        None return, the reason lets scan() tell the user *why* nothing was
        found instead of failing completely silently."""
        try:
            res = requests.get(
                "https://api.keyapi.ai/v1/instagram/web_profile_info",
                params={"username": self.username},
                headers={"Authorization": f"Bearer {KEYAPI_KEY}"},
                timeout=10,
            )
        except Exception as e:
            return None, f"keyapi.ai request failed ({e})"
        if res.status_code != 200:
            return None, f"keyapi.ai returned HTTP {res.status_code}"
        try:
            data = res.json().get("data") or {}
        except ValueError:
            return None, "keyapi.ai returned a non-JSON response"
        # keyapi.ai's response shape wasn't confirmed to nest under "user"
        # the same way Instagram's own endpoint does - accept either.
        user = data.get("user") or data or None
        if not user:
            return None, "keyapi.ai returned no profile data (account likely doesn't exist)"
        return user, None

    def _fetch_direct(self):
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={self.username}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
        except Exception as e:
            return None, f"direct request failed ({e})"
        if res.status_code != 200:
            return None, f"instagram.com returned HTTP {res.status_code} (often a rate-limit/login-wall block)"
        try:
            data = res.json()
        except ValueError:
            return None, "instagram.com returned a non-JSON response"
        user = (data.get("data") or {}).get("user")
        if not user:
            return None, "instagram.com returned no profile data (account likely doesn't exist)"
        return user, None

    def scan(self):
        reasons = []
        user = None
        if KEYAPI_KEY:
            user, reason = self._fetch_via_keyapi()
        else:
            reason = "KEYAPI_KEY not configured"
        if reason:
            reasons.append(reason)

        if not user:
            # Keep the keyapi.ai failure reason above even if the direct
            # fallback also fails - the more informative one (e.g. an auth
            # error on the primary path) shouldn't get masked by a generic
            # fallback failure.
            user, direct_reason = self._fetch_direct()
            if direct_reason:
                reasons.append(direct_reason)

        if not user:
            console.warning("Instagram", " / ".join(reasons) or "no profile data found")
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
