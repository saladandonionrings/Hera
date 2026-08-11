import json

from curl_cffi import requests
from bs4 import BeautifulSoup
from core.display import console


class CalendlyScanner:
    """Extracts profile info from a Calendly public scheduling page - name,
    bio and avatar come from the Open Graph tags Calendly itself sets for
    link unfurling (Slack/Twitter previews etc), so they're reliably
    present on any real, findable profile. Event types (meeting types the
    person offers) are a best-effort pull from JSON-LD structured data when
    the page happens to expose it - not guaranteed, since Calendly doesn't
    commit to one stable markup shape for that across page versions.
    """

    def __init__(self, username):
        self.username = username.strip().lstrip('@')
        self.url = f"https://calendly.com/{self.username}"
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    @staticmethod
    def _meta_content(soup, property_name):
        tag = soup.find("meta", property=property_name)
        return (tag.get("content") or "").strip() if tag else ""

    @staticmethod
    def _clean_name(og_title):
        # "Meet with Jane Doe" / "Jane Doe - Calendly" -> "Jane Doe"
        name = og_title
        if name.lower().startswith("meet with "):
            name = name[len("meet with "):]
        for suffix in (" - Calendly", " | Calendly"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
        return name.strip()

    @staticmethod
    def _extract_event_types(soup):
        """JSON-LD structured data only - a heading/text scan across the
        page is too noisy (nav labels, cookie banners) to trust as "these
        are the meeting types this person offers"."""
        titles = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict) and item.get("@type") in ("Event", "Service") and item.get("name"):
                    titles.append(item["name"])

        seen = set()
        deduped = []
        for t in titles:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        return deduped

    def scan(self):
        try:
            res = self.session.get(self.url, headers=self.headers, timeout=15)
        except Exception as e:
            console.error("Calendly Scraper", str(e))
            return False

        if res.status_code != 200:
            return False

        try:
            soup = BeautifulSoup(res.text, "html.parser")
        except Exception:
            return False

        og_title = self._meta_content(soup, "og:title")
        not_found_markers = ("page not found", "doesn't exist", "does not exist", "we can't find")
        if not og_title or any(m in res.text.lower() for m in not_found_markers):
            return False

        console.module_header("CALENDLY")
        console.success("Calendly Profile", self.url)

        name = self._clean_name(og_title)
        if name:
            console.info("Name", name)

        bio = self._meta_content(soup, "og:description")
        if bio:
            console.info("Bio", bio)

        events = self._extract_event_types(soup)
        if events:
            console.info("Event Types", f"{len(events)} listed")
            for title in events[:8]:
                console.sub_item("Event", title)

        avatar = self._meta_content(soup, "og:image")
        if avatar:
            console.info("", avatar)

        return True
