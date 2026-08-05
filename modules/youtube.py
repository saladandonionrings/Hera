import re

from curl_cffi import requests
from core.display import console


class YouTubeScanner:
    """Extracts channel data from a YouTube handle's public page. Handle
    URLs (@name) are the modern canonical way to look up an arbitrary
    username - legacy /user/ and /c/ custom URLs aren't guaranteed to exist
    for a given handle, so this is the closest thing to a reliable lookup."""

    def __init__(self, username):
        self.username = username
        self.url = f"https://www.youtube.com/@{username}"
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def scan(self):
        try:
            res = self.session.get(self.url, headers=self.headers, timeout=15)
        except Exception as e:
            console.error("YouTube Scraper", str(e))
            return False

        if res.status_code != 200:
            return False

        html = res.text
        # A resolved channel page always embeds its canonical channel ID
        # (UC...) somewhere in the initial data - a handle that doesn't
        # exist renders a generic/search page without one.
        channel_id = re.search(r'"channelId":"(UC[\w-]{22})"', html)
        if not channel_id:
            return False

        console.module_header("YOUTUBE DEEP ANALYSIS")
        console.success("YouTube Channel", self.url)
        console.info("Channel ID", channel_id.group(1))

        title = re.search(r'<meta property="og:title" content="([^"]*)"', html)
        if title:
            console.info("Channel Name", title.group(1))

        description = re.search(r'<meta property="og:description" content="([^"]*)"', html)
        if description:
            console.info("Description", description.group(1)[:300])

        subs = re.search(r'"subscriberCountText":\{"simpleText":"([^"]+)"', html)
        if not subs:
            subs = re.search(r'"subscriberCountText":\{"accessibility":\{"accessibilityData":\{"label":"([^"]+)"', html)
        if subs:
            console.info("Subscribers", subs.group(1))

        videos = re.search(r'"videoCountText":\{"runs":\[\{"text":"([^"]+)"', html)
        if videos:
            console.info("Videos", videos.group(1))

        console.info("Verified", "Yes" if '"isVerified":true' in html else "No")

        avatar = re.search(r'"avatar":\{"thumbnails":\[\{"url":"([^"]+)"', html)
        if avatar:
            console.info("Avatar", avatar.group(1))

        return True
