import os
import sys
import asyncio
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# display and conf
from core.display import console as old_console
from core.config import is_valid_email, is_valid_phone, PROTON_DOMAINS

# OSINT modules
from modules import (
    BlackbirdScanner, 
    GitHubScanner, 
    ProtonScanner, 
    GoogleScanner, 
    EmailSocialScanner, 
    SnapchatScanner,
    WordPressEmailScanner,
    FacebookScanner,
    LeboncoinScanner,
    EAScanner,
    NexonScanner,
    HudsonRockScanner,
    ESPNScanner,
    VivinoScanner,
    SpotifyScanner,
    ChessScanner,
    AdobeScanner,
    DuolingoScanner,
    XvideosScanner,
    TwitterScanner,
    SteamScanner,
    StatsfmScanner,
    ISPScanner,
    AcademiaScanner,
    MojangScanner,
    GitLabScanner,
    LichessScanner,
    HackerNewsScanner,
    NpmScanner,
    DockerHubScanner,
    BitbucketScanner,
    PhoneScanner,
    PicsartScanner,
    TrelloScanner,
    WattpadScanner,
    RobloxScanner,
    ImageshackScanner,
    SmuleScanner,
    PokemonShowdownScanner,
    XboxGamertagScanner,
    LeakCheckScanner
)

# encoding
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

rich_console = Console()

def run_concurrent_checks(checks, target, max_workers=20):
    """Runs a list of (name, scanner) .scan(target) checks concurrently,
    yielding (name, scanner, result) tuples one at a time as each finishes.

    These modules are all I/O-bound (a single blocking HTTP call each) and
    completely independent, so running them sequentially wastes most of the
    scan's wall-clock time waiting on network round-trips one at a time.
    Only scanners that stay silent during .scan() (returning their result
    instead of printing it themselves) belong in this pool: the caller does
    the printing here, one result at a time as as_completed() hands it back
    on the main thread, so results still appear progressively - just as fast
    as the pool can run them instead of one full sequential pass - and
    concurrent completions can never interleave mid-line or corrupt a
    module's own multi-line block."""
    if not checks:
        return
    with ThreadPoolExecutor(max_workers=min(max_workers, len(checks))) as executor:
        future_to_pair = {executor.submit(scanner.scan, target): (name, scanner) for name, scanner in checks}
        for future in as_completed(future_to_pair):
            name, scanner = future_to_pair[future]
            try:
                result = future.result()
            except Exception:
                result = None
            yield name, scanner, result

class EpeiosPro:
    def __init__(self, target):
        self.target = target

    async def scan(self):
        rich_console.print(Panel(f"[bold cyan]TARGET : {self.target}[/bold cyan]", expand=False))
        
        is_email = is_valid_email(self.target)
        is_phone = (not is_email) and is_valid_phone(self.target)
        hr = HudsonRockScanner()

        if is_phone:
            with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
                progress.add_task(description="Scanning phone number...", total=None)
                PhoneScanner(self.target).scan()

        elif is_email:
            is_proton = any(domain in self.target for domain in PROTON_DOMAINS)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                
                progress.add_task(description="Scanning...", total=None)
                
                if is_proton:
                    ProtonScanner().scan(self.target)
                else:
                    GoogleScanner(self.target).scan()
                
                old_console.module_header("📧 Social medias")
                
                EmailSocialScanner(self.target).scan(render_header=False) 
                FacebookScanner(self.target).scan(render_header=False)

                scanners = [
                    ("leboincoin.fr", LeboncoinScanner()),
                    ("ea.com", EAScanner()),
                    ("nexon.com", NexonScanner()),
                    ("espn.com", ESPNScanner()),
                    ("spotify.com", SpotifyScanner()),
                    ("chess.com", ChessScanner()),
                    ("adobe.com", AdobeScanner()),
                    ("duolingo.com", DuolingoScanner()),
                    ("xvideos.com", XvideosScanner()),
                    ("twitter.com", TwitterScanner()),
                    ("academia.edu", AcademiaScanner()),
                    ("imageshack.com", ImageshackScanner())
                ]

                isp = ISPScanner()
                isp_checks = [
                    ("orange.fr", "Account found", isp.check_orange),
                    ("sfr.fr", "Account Found", isp.check_sfr),
                    ("canalplus.com", "Account found", isp.check_mycanal),
                ]
                with ThreadPoolExecutor(max_workers=len(isp_checks)) as executor:
                    futures = {executor.submit(fn, self.target): (name, label) for name, label, fn in isp_checks}
                    for future in as_completed(futures):
                        name, label = futures[future]
                        try:
                            found = future.result()
                        except Exception:
                            found = False
                        if found:
                            old_console.success(name, label)

                for name, _scanner, res in run_concurrent_checks(scanners, self.target):
                    if res is True:
                        old_console.success(name, "Registered")
                    elif res is None and name == "leboncoin.fr":
                        old_console.info(name, "Skipped (DataDome)")

                # Vivino and LeakCheck both print their own multi-line block
                # internally, so they stay out of the concurrent batch above to
                # avoid interleaving with it.
                VivinoScanner().scan(self.target)
                LeakCheckScanner().scan(self.target)

                hr.scan_email(self.target)

                # WordPress Pivot Logic
                wp_pivot = WordPressEmailScanner(self.target)
                found_username = wp_pivot.scan(silent_if_not_found=True)

                GitHubScanner(self.target).scan()

            if found_username:
                rich_console.print(f"\n[bold yellow]! Found username pivot:[/bold yellow] {found_username}")
                pivot_scanner = EpeiosPro(found_username)
                await pivot_scanner.scan()

        else:
            # --- WORKFLOW USERNAME ---
            with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
                progress.add_task(description="Searching username...", total=None)
                
                has_github = BlackbirdScanner(self.target).scan()
                SnapchatScanner(self.target).scan()
                
                if has_github:
                    GitHubScanner(self.target).scan()
                
                username_scanners = [
                    ("steamcommunity.com", SteamScanner()),
                    ("stats.fm", StatsfmScanner()),
                    ("minecraft.net", MojangScanner()),
                    ("gitlab.com", GitLabScanner()),
                    ("lichess.org", LichessScanner()),
                    ("news.ycombinator.com", HackerNewsScanner()),
                    ("npmjs.com", NpmScanner()),
                    ("hub.docker.com", DockerHubScanner()),
                    ("bitbucket.org", BitbucketScanner()),
                    ("smule.com", SmuleScanner()),
                    ("pokemonshowdown.com", PokemonShowdownScanner()),
                    ("xboxgamertag.com", XboxGamertagScanner()),
                    ("picsart.com", PicsartScanner()),
                    ("trello.com", TrelloScanner()),
                    ("wattpad.com", WattpadScanner()),
                    ("roblox.com", RobloxScanner()),
                ]
                default_links = {
                    "picsart.com": f"https://api.picsart.com/users/show/{self.target}.json",
                    "trello.com": f"https://trello.com/{self.target}",
                    "wattpad.com": f"https://www.wattpad.com/user/{self.target}",
                }
                for name, scanner, res in run_concurrent_checks(username_scanners, self.target):
                    if res:
                        value = getattr(scanner, "profile_url", "") or default_links.get(name, "Registered")
                        old_console.success(name, value)

                hr.scan_username(self.target)
                VivinoScanner().scan(self.target)

        rich_console.print(f"\n[cyan]{'─' * 60}[/cyan]\n")

async def run_multiple_targets(targets):
    for current_target in targets:
        epeios = EpeiosPro(current_target)
        await epeios.scan()

def main():
    parser = argparse.ArgumentParser(description="SOCMINT")
    parser.add_argument("target", nargs="?", help="Target Email, Username or Phone number")
    parser.add_argument("-f", "--file", help="Path to a file containing a list of targets")
    args = parser.parse_args()

    os.system('clear' if os.name == 'posix' else 'cls')
    rich_console.print("\n[bold cyan]🕵️‍♂️ 221B Baker Streets[/bold cyan] [dim]v2.0[/dim]\n", justify="center")
    
    targets = []

    if args.file:
        if os.path.exists(args.file):
            with open(args.file, 'r', encoding='utf-8') as f:
                targets = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        else:
            old_console.error("Input Error", f"File '{args.file}' not found.")
            sys.exit(1)
    elif args.target:
        targets = [args.target.strip()]
    else:
        user_input = rich_console.input("[bold] 🎯 Target (Email/Username/Phone) :[/bold] ").strip()
        if user_input: 
            targets = [user_input]

    if not targets:
        old_console.error("Input Error", "No targets provided.")
        sys.exit(1)

    asyncio.run(run_multiple_targets(targets))

if __name__ == "__main__":
    main()