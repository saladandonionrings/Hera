import requests

class AdobeScanner:
    def scan(self, email):
        url = "https://auth.services.adobe.com/signin/v2/users/accounts"
        data = {"username": email, "usernameType": "EMAIL"}
        headers = {
            "X-Ims-Clientid": "homepage_milo",
            "Content-Type": "application/json",
        }
        try:
            r = requests.post(url, json=data, headers=headers, timeout=5)
            if r.status_code == 200 and "authenticationMethods" in r.text:
                return True
            if r.status_code == 404 and "[]" in r.text:
                return False
        except: pass
        return False