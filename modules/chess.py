import requests

class ChessScanner:
    def scan(self, email):
        url = f"https://www.chess.com/callback/email/available?email={email}"
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if r.json().get("available") == False:
                return True
        except: pass
        return False