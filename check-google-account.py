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
    GoogleScanner, 
)

# encoding
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

rich_console = Console()

def run_concurrent_checks(checks, target, max_workers=20):
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