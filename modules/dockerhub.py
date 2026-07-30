import requests

class DockerHubScanner:
    def scan(self, username):
        url = f"https://hub.docker.com/v2/users/{username}/"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return True
        except: pass
        return False
