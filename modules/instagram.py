import requests
from core.display import console


class InstagramScanner:
    """Extracts profile data from Instagram's public web_profile_info API -
    the same endpoint the Instagram web client itself calls, so no login is
    required, just a browser-shaped User-Agent and the public web app id."""

    def __init__(self, username):
        self.username = username
        self.url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "x-ig-app-id": "936619743392459",
            "referer": "https://www.instagram.com/",
            "accept": "*/*",
        }

    def scan(self):
        try:
            res = requests.get(self.url, headers=self.headers, timeout=10)
        except Exception as e:
            console.error("Instagram Scraper", str(e))
            return False

        if res.status_code == 404:
            return False
        if res.status_code != 200:
            # Instagram frequently rate-limits or serves an HTML login wall
            # to requests that look automated - not a real error worth
            # alarming about, just no data available on this attempt.
            return False

        try:
            data = res.json()
        except ValueError:
            return False

        user = (data.get("data") or {}).get("user")
        if not user:
            return False

        console.module_header("INSTAGRAM DEEP ANALYSIS")
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

        if user.get("is_business_account") and user.get("category_name"):
            console.info("Category", user["category_name"])

        external_url = user.get("external_url")
        if external_url:
            console.info("Website", external_url)

        avatar = user.get("profile_pic_url_hd") or user.get("profile_pic_url")
        if avatar:
            console.info("Avatar", avatar)

        return True
