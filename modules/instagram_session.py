import os

from dotenv import load_dotenv

load_dotenv()

SESSION_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instagram_session.json")


def get_authenticated_client():
    """Returns a logged-in instagrapi Client using the saved session (and
    INSTAGRAM_USERNAME/INSTAGRAM_PASSWORD to refresh it if the session has
    gone stale), or None if no Instagram account is configured, instagrapi
    isn't installed, or the login fails."""
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    if not (username and password):
        return None

    try:
        from instagrapi import Client
    except ImportError:
        return None

    cl = Client()
    try:
        if os.path.exists(SESSION_FILE):
            cl.load_settings(SESSION_FILE)
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        return cl
    except Exception:
        return None
