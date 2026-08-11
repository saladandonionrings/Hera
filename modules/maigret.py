import json
import os
import shutil
import subprocess
import tempfile

from core.display import console

FALSE_POSITIVE_SITES = {
    "chaturbate",
    "tinkoff invest",
    "chatujme.cz",
    "reverbnation",
}

ALREADY_COVERED_SITES = {
    "instagram", "twitter", "snapchat", "tiktok", "telegram", "mastodon.social",
    "reddit", "github", "keybase", "replit", "bugcrowd", "twitch", "kick",
    "discord", "steam", "roblox", "chess", "lichess", "genius", "geniusartists",
    "spotify", "soundcloud", "letterboxd", "vimeo", "pinterest", "behance",
    "vsco", "flickr", "tumblr", "tinder", "xvideos", "medium", "wattpad",
    "duolingo", "quora", "slideshare", "goodreads", "buymeacoffee", "patreon",
    "gravatar", "polarsteps", "minecraft", "gitlab", "hackernews", "npm",
    "docker hub", "bitbucket", "smule", "pokemon showdown", "xbox gamertag",
    "picsart", "trello", "youtube", "calendly",
}

EXCLUDED_SITES = FALSE_POSITIVE_SITES | ALREADY_COVERED_SITES

_supports_no_autoupdate = None


def _maigret_supports_no_autoupdate():
    global _supports_no_autoupdate
    if _supports_no_autoupdate is None:
        try:
            help_out = subprocess.run(
                ["maigret", "--help"], capture_output=True, text=True, timeout=15
            ).stdout
            _supports_no_autoupdate = "--no-autoupdate" in (help_out or "")
        except Exception:
            _supports_no_autoupdate = False
    return _supports_no_autoupdate


class MaigretScanner:
    """Runs the `maigret` OSINT username-search tool as a subprocess.

    Maigret ships its own database of thousands of sites and their
    detection logic - Hera doesn't reimplement any of that, it just invokes
    the CLI, reads back the JSON report it writes, and prints whatever it
    found (minus the known false-positive sites above).
    """

    def __init__(self, username, timeout=180):
        self.username = username
        self.timeout = timeout

    def scan(self):
        console.module_header("MAIGRET")

        if shutil.which("maigret") is None:
            console.error("Maigret", "`maigret` not found (pip install maigret).")
            return False

        with tempfile.TemporaryDirectory(prefix="hera-maigret-") as report_dir:
            cmd = [
                "maigret", self.username,
                "--json", "simple",
                "--folderoutput", report_dir,
                "--timeout", "15",
                "--no-progressbar",
                "--no-color",
                "--print-errors",
                "--print-not-found",
            ]
            if _maigret_supports_no_autoupdate():
                cmd.append("--no-autoupdate")

            try:
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
            except subprocess.TimeoutExpired:
                console.warning("Maigret", f"scan timed out after {self.timeout}s.")
                return False
            except FileNotFoundError:
                console.error("Maigret", "`maigret` not found (pip install maigret).")
                return False

            # Maigret sanitizes the username the same way before naming the
            # report file - mirrored here so the path always matches.
            safe_username = self.username.replace('/', '_')
            report_path = os.path.join(report_dir, f"report_{safe_username}_simple.json")

            if not os.path.exists(report_path):
                # The report file is always written (even empty) once maigret
                # reaches the end of a scan, so a missing file means the
                # process didn't get that far - surface why instead of
                # reporting a misleading "not found".
                self._report_run_failure(process)
                return False

            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    results = json.load(f)
            except (json.JSONDecodeError, OSError):
                console.warning("Maigret", "Could not read scan results.")
                return False

        found_any = False
        for site_name, data in sorted(results.items()):
            if site_name.strip().lower() in EXCLUDED_SITES:
                continue
            url = data.get("url_user") or (data.get("status") or {}).get("url", "")
            if not url:
                continue
            console.success(site_name, url)
            found_any = True

        if not found_any:
            errors, checked_clean = self._scan_health(process.stdout)
            # A clean scan reports each site as either found or genuinely
            # not-found; if almost everything instead came back as an error,
            # "not found" would be misleading - the sites were never really
            # reachable to check in the first place.
            if errors > 5 and errors > checked_clean * 2:
                console.warning("Maigret", f"{errors} site checks errored out (network/DNS likely blocked) - results are incomplete.")
            else:
                console.failure("Maigret", "No accounts found.")

        return found_any

    @staticmethod
    def _scan_health(stdout):
        """Counts maigret's per-site result lines (enabled via --print-errors
        / --print-not-found above) to tell a clean "genuinely not found" scan
        apart from one where every request errored out. Plain substring
        counts rather than anchored regexes, since each live-updating result
        line is prefixed with a bare "\\r" (no newline) for the in-place
        terminal redraw, which a line-start anchor won't match."""
        stdout = stdout or ""
        errors = stdout.count("[?] ")
        checked_clean = stdout.count(": Not found!") + stdout.count("Illegal Username Format For This Site!")
        return errors, checked_clean

    def _report_run_failure(self, process):
        """Gives a concrete reason when maigret exits without writing a
        report, instead of leaving the user staring at a bare "not found"
        that could just as easily mean "the whole scan errored out"."""
        stderr = (process.stderr or "").strip()
        stdout = (process.stdout or "").strip()

        if process.returncode != 0:
            tail = (stderr or stdout).strip().splitlines()
            snippet = tail[-1][:160] if tail else f"exit code {process.returncode}"
            console.warning("Maigret", f"scan failed: {snippet}")
        else:
            console.warning("Maigret", "scan finished without producing a report - check network access to target sites.")
