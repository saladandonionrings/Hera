import json
import re

from curl_cffi import requests
from core.display import console


class SoundCloudScanner:
    """Extracts profile data from the `window.__sc_hydration` JSON blob
    SoundCloud embeds in every profile page for its own client-side app to
    read - same data, no separate API client_id needed."""

    def __init__(self, username):
        self.username = username
        self.url = f"https://soundcloud.com/{username}"
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def scan(self):
        try:
            res = self.session.get(self.url, headers=self.headers, timeout=15)
        except Exception as e:
            console.error("SoundCloud", str(e))
            return False

        if res.status_code != 200:
            return False

        match = re.search(r'window\.__sc_hydration\s*=\s*(\[.*?\]);', res.text, re.DOTALL)
        if not match:
            return False

        try:
            hydration = json.loads(match.group(1))
        except json.JSONDecodeError:
            return False

        user_data = next(
            (entry.get("data") for entry in hydration if entry.get("hydratable") == "user"),
            None,
        )
        if not user_data:
            return False

        console.module_header("SOUNDCLOUD")
        console.success("URL", self.url)

        display_name = user_data.get("full_name") or user_data.get("username")
        if display_name:
            console.info("Display Name", display_name)

        bio = user_data.get("description")
        if bio:
            console.info("Bio", bio)

        console.info("Verified", "Yes" if user_data.get("verified") else "No")

        followers = user_data.get("followers_count")
        following = user_data.get("followings_count")
        tracks = user_data.get("track_count")
        stats = []
        if followers is not None: stats.append(f"{followers} followers")
        if following is not None: stats.append(f"{following} following")
        if tracks is not None: stats.append(f"{tracks} tracks")
        if stats:
            console.info("Activity", " / ".join(stats))

        location = ", ".join(p for p in [user_data.get("city"), user_data.get("country_code")] if p)
        if location:
            console.info("Location", location)

        avatar = user_data.get("avatar_url")
        if avatar:
            console.info("Avatar", avatar)

        return True
