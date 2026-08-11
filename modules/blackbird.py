import requests
from bs4 import BeautifulSoup
from core.display import console
import uuid


# Obviously generic/placeholder images aren't worth surfacing as "the
# user's profile picture" - skip them rather than showing a site's default
# silhouette avatar for every unclaimed-looking profile.
AVATAR_SKIP_MARKERS = ("default", "placeholder", "favicon", "sprite", "avatar_anonymous")


def _extract_avatar(html):
    """Best-effort profile picture pull from a fetched page's og:image /
    twitter:image meta tags - the same fields most sites already set for
    link-preview cards, so no site-specific scraping needed."""
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return None
    tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
    if not tag:
        return None
    url = tag.get("content")
    if not url or any(marker in url.lower() for marker in AVATAR_SKIP_MARKERS):
        return None
    return url


class BlackbirdScanner:
    def __init__(self, username):
        self.username = username
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def check_nexon(self):
        """Vérification via l'API interne de Nexon (Email ou Username)"""
        url = "https://www.nexon.com/api/regional-auth/v1.0/no-auth/login/validate"
        headers = {
            "User-Agent": self.headers["User-Agent"],
            "Content-Type": "application/json",
            "X-Arena-Fe-Version": "account-v1.132.0-eaa30e2b",
            "Origin": "https://www.nexon.com",
            "Referer": "https://www.nexon.com/account/en/login"
        }
        payload = {
            "id": self.username,
            "deviceId": str(uuid.uuid4())
        }
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200 and not res.content:
                console.success("🎮 Nexon", f"Account found")
                return True
        except:
            pass
        return False

    def scan(self):
        console.module_header("SOCIAL MEDIAS PRESENCE")
        
        found_any = self.check_nexon()
        targets = [
            # --- socials ---
            # Instagram is not checked here - InstagramScanner (deep analysis
            # module, called separately) is the sole source for it, hitting
            # instagram.com's own API instead of a third-party proxy.
            ("X (Twitter)", f"https://nitter.net/{self.username}", "nitter_check", None),
            ("Snapchat", f"https://www.snapchat.com/add/{self.username}", "text_present", "og:title"),
            # TikTok is not checked here either - TikTokScanner (deep
            # analysis module) is the sole source for it.
            ("Telegram", f"https://t.me/{self.username}", "text_present", "tgme_page_extra"),
            ("Mastodon", f"https://mastodon.social/@{self.username}", "status", 200),
            ("Gab", f"https://gab.com/{self.username}", "text_present", 'property="og:type" content="profile"'),
            # Reddit is not checked here either - RedditScanner (deep
            # analysis module, pulls post/comment history from
            # deletedby.com) is the sole source for it.

            # --- cyber/dev ---
            ("GitHub", f"https://api.github.com/users/{self.username}", "github_api_check", None),
            ("Keybase", f"https://keybase.io/{self.username}", "status", 200),
            ("Replit", f"https://replit.com/@{self.username}", "status", 200),
            ("Bugcrowd", f"https://bugcrowd.com/{self.username}", "bugcrowd_check", None),

            # --- gaming, esport ---
            ("Twitch", f"https://www.twitch.tv/{self.username}", "twitch_check", None),
            ("Kick", f"https://kick.com/api/v1/channels/{self.username}", "status", 200),
            ("Discord", f"https://discord.com/invite/{self.username}", "discord_size_check", 22000),
            ("Steam", f"https://steamcommunity.com/id/{self.username}", "text_present", "g_rgProfileData"),
            ("Roblox", f"https://www.roblox.com/user.aspx?username={self.username}", "url_not_contains", "users/0/profile"),
            ("Tracker.gg", f"https://tracker.gg/valorant/profile/riot/{self.username}/overview", "status", 200),
            ("Chess.com", f"https://www.chess.com/member/{self.username}", "status", 200),
            ("Lichess", f"https://lichess.org/@/{self.username}", "status", 200),

            # --- music, video, cinema ---
            ("Genius (User)", f"https://genius.com/{self.username}", "status", 200),
            ("Genius (Artist)", f"https://genius.com/artists/{self.username}", "status", 200),
            ("Spotify", f"https://open.spotify.com/user/{self.username}", "text_present", "spotify:user:"),
            # SoundCloud is not checked here either - SoundCloudScanner (deep
            # analysis module) is the sole source for it.
            ("Letterboxd", f"https://letterboxd.com/{self.username}/", "status", 200),
            ("Vimeo", f"https://vimeo.com/{self.username}", "status", 200),

            # --- art/pics ---
            ("Pinterest", f"https://www.pinterest.com/{self.username}/", "pinterest_custom_check", None),
            ("Behance", f"https://www.behance.net/{self.username}", "status", 200),
            ("VSCO", f"https://vsco.co/{self.username}/gallery", "status", 200),
            ("Flickr", f"https://www.flickr.com/people/{self.username}/", "status", 200),
            ("Tumblr", f"https://www.tumblr.com/{self.username}", "status", 200),

            # --- dating, adults ---
            ("Tinder", f"https://tinder.com/@{self.username}", "text_not_present", "The person you're looking for may have changed their ID but there are plenty more people to see on Tinder."),
            ("XVideos", f"https://www.xvideos.com/profiles/{self.username}", "status", 200),

            # --- forums, writings ---
            ("Medium", f"https://medium.com/@{self.username}", "text_not_present", "Out of nothing, something."),
            ("Wattpad", f"https://www.wattpad.com/user/{self.username}", "text_not_present", "User not found"),
            ("Duolingo", f"https://www.duolingo.com/profile/{self.username}", "duolingo_check", None),
            ("Quora", f"https://www.quora.com/profile/{self.username}", "text_not_present", "Page Not Found"),
            ("SlideShare", f"https://www.slideshare.net/{self.username}", "text_not_present", "Page no longer exists"),
            ("GoodReads", f"https://www.goodreads.com/{self.username}", "status", 200),

            # --- profiles,links ---
            ("Linktree", f"https://linktr.ee/{self.username}", "status", 200),
            ("BuyMeACoffee", f"https://www.buymeacoffee.com/{self.username}", "text_not_present", "couldn't find that page"),
            ("Patreon", f"https://www.patreon.com/{self.username}", "status", 200),
            ("Gravatar", f"http://en.gravatar.com/{self.username}.json", "text_present", '"profileUrl"'),
            ("Polarsteps", f"https://www.polarsteps.com/{self.username}", "response_url", "user-not-found"),

            # --- gaming, video ---
            ("PSNProfiles", f"https://psnprofiles.com/{self.username}", "text_not_present", "This player could not be found"),
            ("Xbox", f"https://www.xbox.com/en-US/play/user/{self.username}", "status", 200),
            ("VLR.gg", f"https://www.vlr.gg/user/{self.username}", "text_not_present", "Page Not Found"),
            ("JeuxVideo.com", f"https://www.jeuxvideo.com/profil/{self.username}", "text_not_present", "Profil introuvable"),
            ("Dailymotion", f"https://www.dailymotion.com/{self.username}", "status", 200),
            ("BandLab", f"https://www.bandlab.com/{self.username}", "status", 200),
        ]

        found_any = False
        github_found = False
        avatars = []
        session = requests.Session()

        for site, url, check_type, check_val in targets:
            try:
                res = session.get(url, headers=self.headers, timeout=10, allow_redirects=True)
                is_found = False

                if check_type == "status":
                    if res.status_code == 200: is_found = True
                elif check_type == "text_not_present":
                    if res.status_code == 200 and check_val not in res.text: is_found = True
                elif check_type == "text_present":
                    if res.status_code == 200 and check_val in res.text: is_found = True
                elif check_type == "discord_size_check":
                    generic_discord = "Discord - Group Chat That’s All Fun & Games"
                    if res.status_code == 200 and len(res.content) > check_val and generic_discord not in res.text: is_found = True
                elif check_type == "bugcrowd_check":
                    if res.status_code == 200:
                        content_low = res.text.lower()
                        error_msg = "requested page was not found"
                        if self.username.lower() in content_low and error_msg not in content_low: is_found = True
                elif check_type == "github_api_check":
                    if res.status_code == 200 and "login" in res.text:
                        is_found = True
                        github_found = True
                elif check_type == "instagram_header_check":
                    content_type = res.headers.get("Content-Type", "")
                    content_length = int(res.headers.get("Content-Length", 0))
                    if "text/html" in content_type: is_found = True
                    elif res.status_code == 301 and content_length > 0: is_found = True
                elif check_type == "twitch_check":
                    if res.status_code == 200 and f"{self.username}" in res.text: is_found = True
                elif check_type == "youtube_custom_check":
                    if res.status_code == 200 and "404 Not Found" not in res.text and "This page isn't available" not in res.text:
                        is_found = True
                elif check_type == "pinterest_custom_check":
                    # A missing account redirects (via allow_redirects) to
                    # pinterest.com/?show_error=true - that's the reliable
                    # signal, not page text (which varies by locale).
                    if res.status_code == 200 and "show_error=true" not in res.url:
                        is_found = True
                elif check_type == "nitter_check":
                    instances = [f"https://nitter.net/{self.username}", f"https://nitter.cz/{self.username}", f"https://nitter.it/{self.username}"]
                    found_on_any = False
                    for instance_url in instances:
                        try:
                            test_res = requests.get(instance_url, headers=self.headers, timeout=5)
                            content_low = test_res.text.lower()
                            not_found_indicators = ["user not found", "not found", "unavailable", "doesn't exist", "this page doesn’t exist", "empty-feed-header"]
                            if test_res.status_code == 200 and not any(x in content_low for x in not_found_indicators):
                                if self.username.lower() in content_low:
                                    is_found = True
                                    url = instance_url
                                    found_on_any = True
                                    break
                        except: continue
                    is_found = found_on_any
                elif check_type == "breach_check":
                    if res.status_code == 200:
                        content_low = res.text.lower()
                        if "is either invalid or doesn't exist" not in content_low:
                            if self.username.lower() in content_low: is_found = True
                elif check_type == "url_not_contains":
                    if res.status_code == 200 and check_val not in res.url: is_found = True
                elif check_type == "pinterest_size_check":
                    if res.status_code == 200 and len(res.content) > check_val:
                        if self.username.lower() in res.text.lower() and "show_error=true" not in res.url: is_found = True
                elif check_type == "duolingo_check":
                    if res.status_code == 200 and "/errors/" not in res.url and "Learn a language for free" not in res.text: is_found = True

                if is_found:
                    final_url = url
                    if site == "GitHub": final_url = f"https://github.com/{self.username}/"
                    if site == "X (Twitter)": final_url = f"https://x.com/{self.username}"

                    console.success(site, final_url)
                    found_any = True

                    if check_type == "github_api_check":
                        try:
                            avatar_url = res.json().get("avatar_url")
                        except Exception:
                            avatar_url = None
                    elif check_type == "nitter_check":
                        # The page that actually matched is test_res (one of
                        # several mirror instances tried above), not the
                        # outer res, which is still nitter.net's own response.
                        avatar_url = _extract_avatar(test_res.text)
                    else:
                        avatar_url = _extract_avatar(res.text)

                    if avatar_url:
                        avatars.append((site, avatar_url))

            except Exception:
                continue

        if not found_any:
            console.failure("Profiles", f"No profiles found for '{self.username}'")

        if avatars:
            console.module_header("PROFILE PICTURES")
            for site, avatar_url in avatars:
                console.info(f"{site} Avatar", avatar_url)
            
        return github_found