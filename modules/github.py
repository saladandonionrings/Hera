import os
import requests
import re
from core.display import console
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class GitHubScanner:
    def __init__(self, target):
        self.target = target
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        if GITHUB_TOKEN:
            self.headers['Authorization'] = f'token {GITHUB_TOKEN}'

    def get_emails_from_commits(self, username):
        results_map = {}
        repos = []
        try:
            url = f"https://api.github.com/users/{username}/repos?per_page=100"
            res = requests.get(url, headers=self.headers, timeout=10).json()
            if isinstance(res, list):
                for r in res:
                    if not r['fork']: repos.append({'name': r['name'], 'branch': r['default_branch']})
            
            for repo in repos[:5]:
                commit_url = f"https://api.github.com/repos/{username}/{repo['name']}/commits?per_page=10"
                commits = requests.get(commit_url, headers=self.headers, timeout=10).json()
                if not isinstance(commits, list): continue
                
                for c in commits:
                    sha = c['sha']
                    patch_url = f"https://github.com/{username}/{repo['name']}/commit/{sha}.patch"
                    patch_res = requests.get(patch_url, headers=self.headers, timeout=5).text
                    match = re.search(r'^From: (.*?) <(.*?)>', patch_res, re.MULTILINE)
                    if match:
                        email = match.group(2).strip()
                        if "noreply" not in email:
                            results_map[email] = match.group(1).strip()
        except: pass
        return results_map

    def scan(self):
        try:
            username = self.target
            if "@" in self.target:
                search_url = f"https://api.github.com/search/users?q={self.target}"
                s_data = requests.get(search_url, headers=self.headers, timeout=10).json()
                if s_data.get("total_count", 0) > 0: username = s_data["items"][0]["login"]
                else: return

            profile_url = f"https://api.github.com/users/{username}"
            p = requests.get(profile_url, headers=self.headers, timeout=10).json()
            
            if 'login' in p:
                console.module_header("GITHUB DEEP ANALYSIS")
                console.success("GitHub Profile", username)
                
                console.info("Full Name", p.get('name', 'Private'))
                console.info("Location", p.get('location', 'Unknown'))
                console.info("Created on", p.get('created_at', 'Unknown'))
                console.info("Company", p.get('company', 'Unknown'))
                console.info("Website/Blog", p.get('blog', 'None'))
                
                twitter = p.get('twitter_username')
                console.info("Twitter", f"https://twitter.com/{twitter}" if twitter else 'None')
                console.info("Public Repos", p.get('public_repos', 0))
                console.info("Bio", p.get('bio', 'None'))
                
                console.info("Commit History", "Scanning patches for hidden emails...")
                harvested = self.get_emails_from_commits(username)
                if harvested:
                    for mail, name in harvested.items():
                        console.sub_item(mail, name)
                else:
                    console.sub_item("Status", "No unique emails found.")
            else:
                if "@" not in self.target:
                    console.failure("GitHub", "Target not found on GitHub.")
        except Exception as e:
            console.error("GitHub API", str(e))