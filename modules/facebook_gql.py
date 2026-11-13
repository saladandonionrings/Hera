import os
from core.display import console
from dotenv import load_dotenv

load_dotenv()

COOKIES_FILE = os.getenv("FACEBOOK_COOKIES_FILE", "facebook_cookies.json")


class FacebookGqlScanner:
    """Facebook profile lookup via facebook-gql-scraper
    (https://github.com/XD-MHLOO/facebook-gql-scraper), which hits
    Facebook's own internal GraphQL endpoints using a real logged-in
    account's exported session cookies - far richer than the email-only
    account-search FacebookScanner (name, bio, location, hometown,
    relationship, work/education, followers/followees/friends counts...),
    but it needs a real account's cookies (export with a browser extension
    like Cookie-Editor while logged into Facebook) since the GraphQL API
    isn't reachable anonymously."""

    def __init__(self, username):
        self.username = username

    def scan(self):
        console.module_header("FACEBOOK (GraphQL)")

        if not os.path.exists(COOKIES_FILE):
            console.warning(
                "Facebook",
                f"no cookies file configured (export facebook_cookies.json from a logged-in "
                f"browser session, or set FACEBOOK_COOKIES_FILE - looked for '{COOKIES_FILE}')",
            )
            return False

        try:
            import facebook_gql_scraper as fgs
        except ImportError:
            console.warning("Facebook", "facebook-gql-scraper not installed (pip install facebook-gql-scraper)")
            return False

        try:
            ctx = fgs.FacebookContext(cookies_file=COOKIES_FILE, quiet=True)
            user = fgs.Profile.from_username(ctx, username=self.username)
        except fgs.ProfileNotFoundError:
            console.warning("Facebook", "no profile found for this username")
            return False
        except fgs.SessionExpiredError:
            console.warning("Facebook", "session expired - re-export facebook_cookies.json from a logged-in browser")
            return False
        except fgs.FacebookAccessException as e:
            console.warning("Facebook", f"access refused ({e})")
            return False
        except Exception as e:
            console.warning("Facebook", f"lookup failed ({e})")
            return False

        console.success("Facebook Profile", user.url or f"https://www.facebook.com/{self.username}")

        if user.name:
            console.info("Name", user.name)
        if user.alternate_name:
            console.info("Alternate Name", user.alternate_name)
        if user.biography:
            console.info("Bio", user.biography)
        if user.category:
            console.info("Category", user.category)
        if user.current_location:
            console.info("Location", user.current_location)
        if user.hometown:
            console.info("Hometown", user.hometown)
        if user.birthday:
            console.info("Birthday", user.birthday)

        console.info("Verified", "Yes" if user.is_verified else "No")

        stats = []
        if user.followers_count:
            stats.append(f"{user.followers_count} followers")
        if user.followees_count:
            stats.append(f"{user.followees_count} following")
        if user.friends_count:
            stats.append(f"{user.friends_count} friends")
        if stats:
            console.info("Activity", " / ".join(stats))

        works = [w.get("company") for w in (user.works or []) if w.get("company")]
        if works:
            console.info("Works", ", ".join(works))

        colleges = [c.get("name") for c in (user.colleges or []) if c.get("name")]
        if colleges:
            console.info("Education", ", ".join(colleges))

        if user.profile_picture_url:
            console.info("", user.profile_picture_url)

        return True
