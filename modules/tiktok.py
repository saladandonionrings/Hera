import json
import re

from curl_cffi import requests
from core.display import console


class TikTokScanner:
    """Extracts profile data from TikTok's own embedded page state - the
    same __UNIVERSAL_DATA_FOR_REHYDRATION__ (or legacy SIGI_STATE) JSON
    blob TikTok's web client hydrates itself from, no API key needed."""

    def __init__(self, username):
        self.username = username.strip().lstrip('@')
        self.url = f"https://www.tiktok.com/@{self.username}"
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.mobile_headers = {
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 musical_ly_40.6.0 BytedanceWebview/d8a21c6",
            "Accept": "text/html",
        }

    def _extract_user_data(self, html):
        universal = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>([^<]+)</script>', html)
        if universal:
            data = json.loads(universal.group(1))
            default_scope = data.get("__DEFAULT_SCOPE__") or {}
            return (default_scope.get("webapp.user-detail") or {}).get("userInfo")

        sigi = re.search(r'<script id="SIGI_STATE"[^>]*>([^<]+)</script>', html)
        if sigi:
            data = json.loads(sigi.group(1))
            user_module = data.get("UserModule") or {}
            users = user_module.get("users") or {}
            if users:
                key = next(iter(users))
                stats = user_module.get("stats") or {}
                return {"user": users[key], "stats": stats.get(key)}

        return None

    def _fetch_region(self):
        """A second request with mobile (TikTok app webview) headers surfaces
        a region field the desktop response doesn't include."""
        try:
            res = self.session.get(
                f"{self.url}?isUniqueId=true&isSecured=true",
                headers=self.mobile_headers,
                timeout=15,
            )
        except Exception:
            return None
        if res.status_code != 200:
            return None

        marker = f'"uniqueId":"{self.username}"'
        idx = res.text.find(marker)
        block = res.text[idx:idx + 10000] if idx != -1 else res.text
        match = re.search(r'"region":"(.*?)"', block)
        return match.group(1) if match else None

    def scan(self):
        try:
            res = self.session.get(self.url, headers=self.headers, timeout=15)
        except Exception as e:
            console.error("TikTok Scraper", str(e))
            return False

        if res.status_code != 200:
            return False

        try:
            raw = self._extract_user_data(res.text)
        except (json.JSONDecodeError, AttributeError, KeyError):
            return False

        if not raw or not raw.get("user"):
            return False

        user = raw["user"]
        stats = raw.get("stats") or {}

        console.module_header("TIKTOK")
        console.success("TikTok Profile", self.url)

        nickname = user.get("nickname")
        if nickname:
            console.info("Display Name", nickname)

        bio = user.get("signature")
        if bio:
            console.info("Bio", bio)

        console.info("Verified", "Yes" if user.get("verified") else "No")
        console.info("Private Account", "Yes" if user.get("privateAccount") else "No")

        followers = stats.get("followerCount")
        following = stats.get("followingCount")
        likes = stats.get("heartCount")
        videos = stats.get("videoCount")
        activity = []
        if followers is not None: activity.append(f"{followers} followers")
        if following is not None: activity.append(f"{following} following")
        if likes is not None: activity.append(f"{likes} likes")
        if videos is not None: activity.append(f"{videos} videos")
        if activity:
            console.info("Activity", " / ".join(activity))

        region = self._fetch_region()
        if region:
            console.info("Region", region)

        avatar = user.get("avatarLarger") or user.get("avatarMedium") or user.get("avatarThumb")
        if avatar:
            console.info("", avatar)

        return True
