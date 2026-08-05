import requests
from core.display import console

class LeakCheckScanner:
    def scan(self, email):
        url = f"https://leakcheck.io/api/public?check={requests.utils.quote(email)}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return False

            data = r.json()
            if not data.get("success"):
                return False

            names = [s.get("name", "").strip() for s in (data.get("sources") or []) if s.get("name")]
            if not names:
                return False

            console.module_header("LeakCheck")
            console.warning("Status", f"Found in {len(names)} breach(es)")

            fields = data.get("fields") or []
            if fields:
                console.info("Exposed Data", ", ".join(fields))

            preview = names[:25]
            suffix = f" (+{len(names) - 25} more)" if len(names) > 25 else ""
            console.info("Breaches", ", ".join(preview) + suffix)
            return True
        except Exception:
            return False
