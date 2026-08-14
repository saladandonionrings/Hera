import os
import re
import requests
from core.display import console
from core.scrape import extract_profile_meta, print_profile_meta
from dotenv import load_dotenv
import uuid

load_dotenv()
KEYAPI_KEY = os.getenv("KEYAPI_KEY")


class BlackbirdScanner:
    def __init__(self, username):
        self.username = username
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def check_pinterest_keyapi(self):
        """Pinterest existence via keyapi.ai's search endpoint - which is a
        fuzzy search, not an exact-username lookup, so it happily returns
        similar-looking accounts (e.g. a lookalike username with a capital
        "I" swapped for a lowercase "l") for a query that doesn't actually
        exist. Only a case-insensitive exact match on the returned
        username counts as a hit; the old pinterest_custom_check below
        (still used as a fallback when no KEYAPI_KEY is configured) is kept
        for when no key is set."""
        try:
            res = requests.get(
                "https://api.keyapi.ai/v1/pinterest/search",
                params={"username": self.username},
                headers={"Authorization": f"Bearer {KEYAPI_KEY}"},
                timeout=10,
            )
            if res.status_code != 200:
                return False, {}
            users = ((res.json().get("data") or {}).get("users")) or []
            target = self.username.strip().lower()
            user = next((u for u in users if (u.get("username") or "").strip().lower() == target), None)
            if not user:
                return False, {}
        except Exception:
            return False, {}

        meta = {}
        avatar = (user.get("image_xlarge_url") or user.get("image_large_url")
                  or user.get("image_medium_url") or user.get("image_small_url"))
        if avatar:
            meta["avatar"] = avatar
        if user.get("full_name"):
            meta["name"] = user["full_name"]

        stats = []
        if user.get("follower_count") is not None:
            stats.append(f"{user['follower_count']} followers")
        if user.get("pin_count") is not None:
            stats.append(f"{user['pin_count']} pins")
        if user.get("board_count") is not None:
            stats.append(f"{user['board_count']} boards")
        if stats:
            meta["stats"] = " / ".join(stats)

        return True, meta

    def check_twitter_keyapi(self):
        """X/Twitter existence via keyapi.ai's screenname endpoint, which
        returns the live profile record (avatar, name, bio, follower/
        following/tweet counts) straight from X's internal API - the old
        nitter_check below (still used as a fallback when no KEYAPI_KEY is
        configured) instead scrapes third-party nitter mirrors, which
        rate-limit or go down unpredictably."""
        try:
            res = requests.get(
                "https://api.keyapi.ai/v1/twitter/screenname",
                params={"screenname": self.username},
                headers={"Authorization": f"Bearer {KEYAPI_KEY}"},
                timeout=10,
            )
            if res.status_code != 200:
                return False, {}
            data = res.json().get("data") or {}
            if not data.get("profile") and not data.get("id"):
                return False, {}
        except Exception:
            return False, {}

        meta = {}
        if data.get("avatar"):
            meta["avatar"] = data["avatar"]
        if data.get("name"):
            meta["name"] = data["name"]
        if data.get("desc"):
            meta["bio"] = data["desc"]
        if data.get("location"):
            meta["location"] = data["location"]

        stats = []
        if data.get("sub_count") is not None:
            stats.append(f"{data['sub_count']} followers")
        if data.get("friends") is not None:
            stats.append(f"{data['friends']} following")
        if data.get("statuses_count") is not None:
            stats.append(f"{data['statuses_count']} tweets")
        if stats:
            meta["stats"] = " / ".join(stats)

        return True, meta

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
            ("X (Twitter)", f"https://x.com/{self.username}", "x_check", None),
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
            # A missing Replit account still returns 200 but with the site's
            # generic default og:image instead of a real avatar - that image
            # URL showing up in the page is the reliable "doesn't exist"
            # signal, not the status code.
            ("Replit", f"https://replit.com/@{self.username}", "text_not_present", "https://replit.com/public/images/opengraph_rebrand.jpg"),
            ("Bugcrowd", f"https://bugcrowd.com/{self.username}", "bugcrowd_check", None),

            # --- gaming, esport ---
            ("Twitch", f"https://www.twitch.tv/{self.username}", "twitch_check", None),
            ("Kick", f"https://kick.com/api/v1/channels/{self.username}", "status", 200),
            ("Discord", f"https://discord.com/invite/{self.username}", "discord_size_check", 22000),
            ("Steam", f"https://steamcommunity.com/id/{self.username}", "text_present", "g_rgProfileData"),
            ("Roblox", f"https://www.roblox.com/user.aspx?username={self.username}", "url_not_contains", "users/0/profile"),
            ("Faceit", f"https://www.faceit.com/en/players/{self.username}", "status", 200),
            ("Tracker.gg", f"https://tracker.gg/valorant/profile/riot/{self.username}/overview", "status", 200),
            ("Chess.com", f"https://www.chess.com/member/{self.username}", "status", 200),
            ("Lichess", f"https://lichess.org/@/{self.username}", "status", 200),

            # --- music, video, cinema ---
            ("Genius (User)", f"https://genius.com/{self.username}", "status", 200),
            ("Genius (Artist)", f"https://genius.com/artists/{self.username}", "status", 200),
            # A missing/private Spotify user still returns 200 with
            # "spotify:user:" present in the page's client-side routing
            # template regardless of the username (false positives) - the
            # page's title falling back to Spotify's generic web-player
            # branding instead of a real display name is the reliable
            # "doesn't exist" signal. Also means real profile info
            # (avatar/name) gets pulled in automatically on a hit, same as
            # every other text_not_present-checked site.
            ("Spotify", f"https://open.spotify.com/user/{self.username}", "text_not_present", "Spotify - Web Player: Music for everyone"),
            # SoundCloud is not checked here either - SoundCloudScanner (deep
            # analysis module) is the sole source for it.
            ("Letterboxd", f"https://letterboxd.com/{self.username}/", "status", 200),
            ("Vimeo", f"https://vimeo.com/{self.username}", "status", 200),

            # --- art/pics ---
            ("Pinterest", f"https://www.pinterest.com/{self.username}/", "pinterest_check", None),
            ("Behance", f"https://www.behance.net/{self.username}", "status", 200),
            ("VSCO", f"https://vsco.co/{self.username}/gallery", "status", 200),
            ("Flickr", f"https://www.flickr.com/people/{self.username}/", "status", 200),
            ("Tumblr", f"https://www.tumblr.com/{self.username}", "status", 200),

            # --- dating, adults ---
            ("Tinder", f"https://tinder.com/@{self.username}", "text_not_present", "The person you're looking for may have changed their ID but there are plenty more people to see on Tinder."),
            ("XVideos", f"https://www.xvideos.com/profiles/{self.username}", "status", 200),
            ("Pornhub", f"https://www.pornhub.com/users/{self.username}", "status", 200),

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
            # Was "response_url", a check_type that was never actually
            # implemented in the dispatch below - Polarsteps never reported
            # a hit no matter what. "url_not_contains" does exactly what
            # was intended here (missing accounts redirect to a URL
            # containing "user-not-found") and already exists below.
            ("Polarsteps", f"https://www.polarsteps.com/{self.username}", "url_not_contains", "user-not-found"),
            ("TripAdvisor", f"https://www.tripadvisor.com/Profile/{self.username}", "status", 200),

            # --- gaming, video ---
            ("PSNProfiles", f"https://psnprofiles.com/{self.username}", "text_not_present", "This player could not be found"),
            ("Fortnite Tracker", f"https://fortnitetracker.com/profile/all/{self.username}", "status", 200),
            # Xbox is not checked here either - the xbox.com/play/user/
            # page returns 200 regardless of whether the gamertag exists
            # (false positives). XboxGamertagScanner (run separately in
            # main.py's username_scanners) hits xboxgamertag.com/search/
            # instead, which actually distinguishes found from not-found.
            ("VLR.gg", f"https://www.vlr.gg/user/{self.username}", "text_not_present", "Page Not Found"),
            ("JeuxVideo.com", f"https://www.jeuxvideo.com/profil/{self.username}", "text_not_present", "Profil introuvable"),
            # A missing Dailymotion account 404s on the /user/ path - the
            # bare https://www.dailymotion.com/{username} page returns 200
            # regardless of whether the account exists (false positives).
            ("Dailymotion", f"https://www.dailymotion.com/user/{self.username}", "status", 200),
            # Same as Replit above - a missing BandLab account still
            # returns 200 with the site's generic default og:image.
            ("BandLab", f"https://www.bandlab.com/{self.username}", "text_not_present", "https://www.bandlab.com/web-app/images/open-graph-4fd21aa09f.png"),
        ]

        found_any = False
        github_found = False
        avatars = []
        session = requests.Session()

        for site, url, check_type, check_val in targets:
            try:
                if check_type == "pinterest_check":
                    is_found, meta = self.check_pinterest_keyapi() if KEYAPI_KEY else (False, {})
                    if not is_found and not KEYAPI_KEY:
                        # No API key configured - fall back to the old
                        # redirect heuristic (missing accounts redirect, via
                        # allow_redirects, to pinterest.com/?show_error=true).
                        res = session.get(url, headers=self.headers, timeout=10, allow_redirects=True)
                        if res.status_code == 200 and "show_error=true" not in res.url:
                            is_found = True
                            meta = extract_profile_meta(res.text)
                    if is_found:
                        console.success(site, url)
                        found_any = True
                        print_profile_meta(meta)
                        if meta.get("avatar"):
                            avatars.append((site, meta["avatar"]))
                    continue

                if check_type == "x_check":
                    is_found, meta = self.check_twitter_keyapi() if KEYAPI_KEY else (False, {})
                    if not is_found and not KEYAPI_KEY:
                        # No API key configured - fall back to scraping
                        # third-party nitter mirrors for the profile page.
                        instances = [f"https://nitter.net/{self.username}", f"https://nitter.cz/{self.username}", f"https://nitter.it/{self.username}"]
                        for instance_url in instances:
                            try:
                                test_res = requests.get(instance_url, headers=self.headers, timeout=5)
                                content_low = test_res.text.lower()
                                not_found_indicators = ["user not found", "not found", "unavailable", "doesn't exist", "this page doesn’t exist", "empty-feed-header"]
                                if test_res.status_code == 200 and not any(x in content_low for x in not_found_indicators):
                                    if self.username.lower() in content_low:
                                        is_found = True
                                        meta = extract_profile_meta(test_res.text)
                                        break
                            except Exception:
                                continue
                    if is_found:
                        console.success(site, url)
                        found_any = True
                        print_profile_meta(meta)
                        if meta.get("avatar"):
                            avatars.append((site, meta["avatar"]))
                    continue

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

                    console.success(site, final_url)
                    found_any = True

                    if check_type == "github_api_check":
                        try:
                            data = res.json()
                            meta = {
                                "avatar": data.get("avatar_url"),
                                "name": data.get("name"),
                                "bio": data.get("bio"),
                            }
                        except Exception:
                            meta = {}
                    else:
                        meta = extract_profile_meta(res.text)
                        if site == "Polarsteps":
                            # Polarsteps doesn't set a useful og:title (no
                            # real display name) - the actual name only
                            # shows up in a CSS-module-hashed class like
                            # "UserWidget-module_name__aB3dE", so match on
                            # the stable prefix and ignore the random suffix.
                            name_match = re.search(
                                r'class="UserWidget-module_name[^"]*"[^>]*>([^<]+)<', res.text
                            )
                            if name_match:
                                meta["name"] = name_match.group(1).strip()

                    print_profile_meta(meta)
                    if meta.get("avatar"):
                        avatars.append((site, meta["avatar"]))

            except Exception:
                continue

        if not found_any:
            console.failure("Profiles", f"No profiles found for '{self.username}'")

        if avatars:
            console.module_header("PROFILE PICTURES")
            for site, avatar_url in avatars:
                console.info(f"{site} Avatar", avatar_url)
            
        return github_found