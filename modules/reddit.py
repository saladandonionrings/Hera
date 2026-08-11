import json
import re
from datetime import datetime, timezone

from curl_cffi import requests
from core.display import console


def _extract_json_object(text, start):
    """text[start] must be '{'. Walks forward tracking string literals (so
    braces inside string values don't throw off the count) and returns the
    balanced object substring."""
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return None


class RedditScanner:
    """Extracts Reddit post/comment history - including content since
    deleted or removed - from deletedby.com's profile page.

    The page is a Next.js App Router page, so the actual profile data isn't
    in a simple embedded JSON tag: it's shipped as a React Server Components
    "Flight" stream, one or more `self.__next_f.push([1, "..."])` calls each
    carrying a JS string literal. That string, once JS-unescaped, contains a
    plain (if unusually shaped) JSON payload with the "initial" profile
    object inside it - so this needs two decode passes, not one.
    """

    def __init__(self, username):
        username = username.strip()
        if username.lower().startswith('u/'):
            username = username[2:]
        self.username = username
        self.url = f"https://deletedby.com/user/{self.username}"
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _extract_initial(self, html):
        for raw in re.findall(r'self\.__next_f\.push\(\[1,"((?:\\.|[^"\\])*)"\]\)', html):
            try:
                decoded = json.loads('"' + raw + '"')
            except (json.JSONDecodeError, ValueError):
                continue

            idx = decoded.find('"initial":')
            if idx == -1:
                continue
            brace_start = decoded.find('{', idx)
            if brace_start == -1:
                continue
            obj_str = _extract_json_object(decoded, brace_start)
            if not obj_str:
                continue
            try:
                return json.loads(obj_str)
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _fmt_date(ts):
        if not ts:
            return None
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%d %b %Y')
        except (ValueError, OSError, OverflowError):
            return None

    def scan(self):
        try:
            res = self.session.get(self.url, headers=self.headers, timeout=15)
        except Exception as e:
            console.error("Reddit Scraper", str(e))
            return False

        if res.status_code == 404:
            return False
        if res.status_code != 200:
            return False

        try:
            initial = self._extract_initial(res.text)
        except Exception:
            return False

        if not initial or not initial.get("username"):
            return False

        posts = initial.get("posts") or []
        comments = initial.get("comments") or []
        insights = initial.get("insights") or {}
        summary = insights.get("summary") or {}

        console.module_header("REDDIT")
        console.success("Reddit History", self.url)

        total = initial.get("count", len(posts) + len(comments))
        console.info("Total Items", f"{total} ({len(posts)} posts, {len(comments)} comments)")

        active_subs = summary.get("activeSubreddits")
        if active_subs is not None:
            console.info("Active Subreddits", str(active_subs))

        top_sub = summary.get("topSubreddit")
        if top_sub:
            console.info("Top Subreddit", f"r/{top_sub}")

        top_hour = summary.get("topHourUtc")
        if top_hour is not None:
            console.info("Most Active", f"~{top_hour}:00 UTC")

        first_seen = self._fmt_date(summary.get("firstSeenUtc"))
        last_seen = self._fmt_date(summary.get("lastSeenUtc"))
        if first_seen:
            console.info("First Seen", first_seen)
        if last_seen:
            console.info("Last Seen", last_seen)

        # The whole point of this source over reddit.com directly - content
        # a moderator, spam filter, or Reddit itself took down, but a copy
        # still exists here.
        removed = [
            item for item in (posts + comments)
            if item.get("removalKind") not in (None, "live")
        ]
        console.info("Removed/Deleted Items", str(len(removed)))

        removed.sort(key=lambda i: i.get("createdUtc", 0), reverse=True)
        for item in removed[:5]:
            label = item.get("title") or (item.get("body") or "")[:80]
            kind = {"mod": "removed by mod", "spam_filter": "held by spam filter"}.get(
                item.get("removalKind"), item.get("removalKind")
            )
            sub = item.get("subreddit", "?")
            console.sub_item(f"r/{sub} ({kind})", label)
        if len(removed) > 5:
            console.sub_item("...", f"and {len(removed) - 5} more removed/deleted items")

        return True
