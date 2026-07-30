import requests
import re
import json

from core.display import console

class SnapchatScanner:
    """Extracts deep OSINT data from Snapchat profiles via hidden JSON."""
    def __init__(self, username):
        self.username = username
        self.url = f"https://www.snapchat.com/add/{self.username}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        self.json_regex = r'<script[^>]+type="application/json"[^>]*>(.*?)</script>'

    def get_value(self, data, path, default="None"):
        """Helper to safely traverse the nested JSON dictionary."""
        keys = path.split('.')
        val = data
        for k in keys:
            if isinstance(val, dict) and k in val: 
                val = val[k]
            else: 
                return default
        return val

    def scan(self):
        try:
            res = requests.get(self.url, headers=self.headers, timeout=10)
            if res.status_code != 200: 
                return False

            # Extract the JSON payload
            match = re.search(self.json_regex, res.text, re.DOTALL)
            if not match: 
                return False

            json_data = json.loads(match.group(1))
            page_title = self.get_value(json_data, "props.pageProps.pageMetadata.pageTitle")
            if page_title == "None" or "Not Found" in page_title: 
                return False

            console.module_header("SNAPCHAT DEEP ANALYSIS")
            console.success("Snapchat Profile", self.username)

            page_type = self.get_value(json_data, "props.pageProps.pageMetadata.pageType")
            is_public = (page_type == 18)

            console.info("Account Type", "Public" if is_public else "Private")
            console.info("Page Title", page_title)

            if is_public:
                base_path = "props.pageProps.userProfile.publicProfileInfo"
                display_name = self.get_value(json_data, f"{base_path}.title") 
                subscribers = self.get_value(json_data, f"{base_path}.subscriberCount")
                bio = self.get_value(json_data, f"{base_path}.bio")
                website = self.get_value(json_data, f"{base_path}.websiteUrl")
                snapcode = self.get_value(json_data, f"{base_path}.snapcodeImageUrl")
                
                console.info("Display Name", display_name)
                console.info("Subscribers", subscribers)
                console.info("Bio", bio)
                
                if website != "None": 
                    console.info("Website", website)
                    
                console.info("Snapcode URL", snapcode)
                
                stories = self.get_value(json_data, "props.pageProps.story.snapList", [])
                highlights = self.get_value(json_data, "props.pageProps.curatedHighlights", [])
                spotlights = self.get_value(json_data, "props.pageProps.spotlightHighlights", [])
                lenses = self.get_value(json_data, "props.pageProps.lenses", [])
                
                console.info("Active Stories", len(stories) if isinstance(stories, list) else 0)
                console.info("Highlights", len(highlights) if isinstance(highlights, list) else 0)
                
                spotlight_count = len(spotlights) if isinstance(spotlights, list) else 0
                console.info("Spotlights", spotlight_count)
                
                if spotlight_count > 0:
                    for i, spot in enumerate(spotlights):
                        if i >= 5:
                            console.sub_item("...", f"et {spotlight_count - 5} autres vidéos ignorées.")
                            break
                        try:
                            snaps = spot.get("snapList", [])
                            if snaps and isinstance(snaps, list):
                                media_url = snaps[0].get("snapUrls", {}).get("mediaUrl", "")
                                if media_url:
                                    console.sub_item(f"Video {i+1}", media_url)
                        except:
                            pass

                console.info("Lenses", len(lenses) if isinstance(lenses, list) else 0)

            else:
                base_path = "props.pageProps.userProfile.userInfo"
                display_name = self.get_value(json_data, f"{base_path}.displayName")
                avatar = self.get_value(json_data, f"{base_path}.bitmoji3d.avatarImage.url")
                snapcode = self.get_value(json_data, f"{base_path}.snapcodeImageUrl")
                
                console.info("Display Name", display_name)
                if avatar != "None": 
                    console.info("Bitmoji 3D", avatar)
                console.info("Snapcode URL", snapcode)

            return True

        except Exception as e:
            console.error("Snapchat Scraper", str(e))
            return False