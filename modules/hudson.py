import requests
import sys
from core.display import console

class HudsonRockScanner:
    def __init__(self):
        self.base_url = "https://cavalier.hudsonrock.com/api/json/v2/osint-tools"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }

    def scan_email(self, email):
        url = f"{self.base_url}/search-by-email?email={email}"
        return self._execute(url, email)

    def scan_username(self, username):
        url = f"{self.base_url}/search-by-username?username={username}"
        return self._execute(url, username)

    def _execute(self, url, target):
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            if res.status_code != 200:
                return False
            
            data = res.json()
            stealers_list = data.get("stealers", [])

            if not stealers_list:
                return False

            console.module_header("HUDSON ROCK - STEALER LOGS")
            print(f" {console.RED}{console.BOLD}‼ {console.RESET} : {len(stealers_list)} Infections found for {target}")
            sys.stdout.flush()

            for i, log in enumerate(stealers_list, 1):
                date = log.get('date_compromised', 'N/A').split('T')[0]
                comp_name = log.get('computer_name', 'Unknown')
                os_sys = log.get('operating_system', 'Unknown')
                ip = log.get('ip', 'Unknown')
                path = log.get('malware_path', 'Not Found')
                
                av_list = log.get('antiviruses', [])
                avs = ", ".join(av_list) if av_list else "None detected"

                # Bloc principal en CYAN
                print(f"\n {console.CYAN}┌── Machine {console.BOLD}#{i}{console.RESET} {console.CYAN}" + "─" * 40)
                print(f" {console.CYAN}│ {console.RESET}💻 {console.BOLD}ID       {console.RESET}: {console.YELLOW}{comp_name}")
                print(f" {console.CYAN}│ {console.RESET}🖥️  {console.BOLD}System   {console.RESET}: {os_sys} (AV: {avs})")
                print(f" {console.CYAN}│ {console.RESET}🌍 {console.BOLD}Network  {console.RESET}: IP: {console.CYAN}{ip}")
                print(f" {console.CYAN}│ {console.RESET}📅 {console.BOLD}Infected {console.RESET}: {date}")
                
                if path and path != "Not Found":
                    print(f" {console.CYAN}│ {console.RESET}🛡️  {console.BOLD}Path     {console.RESET}: {console.RED}{path}")

                pwds = log.get('top_passwords', [])
                logins = log.get('top_logins', [])
                
                if logins:
                    l_str = " | ".join([str(l) for l in logins if l][:3])
                    print(f" {console.CYAN}│ {console.RESET}👤 {console.BOLD}Logins   {console.RESET}: {l_str}...")

                if pwds:
                    p_str = " | ".join([f"[{p}]" for p in pwds if p][:4])
                    print(f" {console.CYAN}│ {console.RESET}🔑 {console.BOLD}Passwords{console.RESET}: {p_str}")

                corp = log.get('total_corporate_services', 0)
                user = log.get('total_user_services', 0)
                print(f" {console.CYAN}│ {console.RESET}📊 {console.BOLD}Impact   {console.RESET}: {console.RED}{corp} Corp {console.RESET}/ {console.RED}{user} User services")
                
                print(f" {console.CYAN}└" + "─" * 53 + f"{console.RESET}")
                sys.stdout.flush()

            print("\n")
            return True

        except Exception as e:
            print(f" [!] Hudson Rock Error: {str(e)}")
            return None