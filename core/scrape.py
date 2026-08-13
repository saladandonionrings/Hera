import re

from bs4 import BeautifulSoup

from core.display import console

# Obviously generic/placeholder images aren't worth surfacing as "the
# user's profile picture" - skip them rather than showing a site's default
# silhouette avatar for every unclaimed-looking profile.
AVATAR_SKIP_MARKERS = ("default", "placeholder", "favicon", "sprite", "avatar_anonymous")

# A title tag/og:title is usually "Display Name (@handle) / Site Name" or
# "Display Name - Site Name" - only the part before the first separator is
# an actual display name, the rest is boilerplate site branding.
_TITLE_SEPARATORS = re.compile(r"\s*[|–—]\s*|\s+-\s+|\s*/\s*|\s*•\s*")


def extract_profile_meta(html):
    """Best-effort profile info (avatar, display name, bio) pulled from a
    fetched page's Open Graph / Twitter Card meta tags - the same fields
    most sites already set for link-preview cards, so no site-specific
    scraping is needed. Each field is simply absent from the returned dict
    if the page didn't have it."""
    meta = {}
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return meta

    img_tag = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
    if img_tag:
        url = (img_tag.get("content") or "").strip()
        if url and not any(marker in url.lower() for marker in AVATAR_SKIP_MARKERS):
            meta["avatar"] = url

    title_tag = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
    if title_tag:
        raw = (title_tag.get("content") or "").strip()
        name = _TITLE_SEPARATORS.split(raw, maxsplit=1)[0].strip()
        if name:
            meta["name"] = name[:120]

    desc_tag = (soup.find("meta", property="og:description")
                or soup.find("meta", attrs={"name": "twitter:description"})
                or soup.find("meta", attrs={"name": "description"}))
    if desc_tag:
        desc = (desc_tag.get("content") or "").strip()
        if desc:
            meta["bio"] = desc[:220]

    return meta


def print_profile_meta(meta):
    """Attaches whatever extract_profile_meta (or a module's own API-field
    mapping) found to the success line printed just before this call, via
    console.sub_item - the frontend promotes these into the found site's
    own result card (avatar/name/bio) instead of a bare link.

    `meta` may carry any of: avatar, name, bio - plus a handful of optional
    extras (location, joined, stats) that some modules can pull straight
    from a JSON API response without a page fetch. `stats` is printed under
    the "Activity" key (e.g. "1,234 followers / 56 posts") - the frontend
    renders that exact key as a row of stat chips on the resulting card."""
    if meta.get("avatar"):
        console.sub_item("Avatar", meta["avatar"])
    if meta.get("name"):
        console.sub_item("Name", meta["name"])
    if meta.get("bio"):
        console.sub_item("Bio", meta["bio"])
    if meta.get("location"):
        console.sub_item("Location", meta["location"])
    if meta.get("joined"):
        console.sub_item("Joined", meta["joined"])
    if meta.get("stats"):
        console.sub_item("Activity", meta["stats"])
