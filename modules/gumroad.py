from curl_cffi import requests


class GumroadScanner:
    """Account existence via Gumroad's forgot-password flow (an Inertia.js
    app): submitting the form returns a flash message saying "An account
    does not exist with that email" when it's unregistered, and something
    else (a generic "check your inbox" confirmation) when it is - a classic
    account-enumeration signal, same shape as EAScanner's approach.
    """

    NEW_URL = "https://gumroad.com/users/forgot_password/new"
    SUBMIT_URL = "https://gumroad.com/users/forgot_password"

    def __init__(self):
        self.session = requests.Session(impersonate="chrome110")
        self.headers = {
            "Accept": "text/html, application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Inertia": "true",
            "X-Requested-With": "XMLHttpRequest",
        }

    def scan(self, email):
        try:
            page = self.session.get(self.NEW_URL, headers=self.headers, timeout=15)
            data = page.json()
        except Exception:
            return None

        csrf_token = (data.get("props") or {}).get("authenticity_token")
        if not csrf_token:
            return None

        post_headers = dict(self.headers)
        post_headers.update({
            "X-CSRF-Token": csrf_token,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": self.NEW_URL,
        })
        inertia_version = page.headers.get("X-Inertia-Version")
        if inertia_version:
            post_headers["X-Inertia-Version"] = inertia_version

        try:
            res = self.session.post(
                self.SUBMIT_URL,
                data={"user[email]": email},
                headers=post_headers,
                timeout=15,
            )
            result = res.json()
        except Exception:
            return None

        message = ((result.get("props") or {}).get("flash") or {}).get("message", "")
        if not message:
            return None

        return "does not exist" not in message.lower()
