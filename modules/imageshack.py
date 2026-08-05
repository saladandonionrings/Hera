import requests

class ImageshackScanner:
    def scan(self, email):
        url = "https://imageshack.com/rest_api/v2/user"
        data = f"email={requests.utils.quote(email)}&username=user&password=1&set_cookies=true"
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        try:
            r = requests.post(url, data=data, headers=headers, timeout=5)
            if r.status_code == 400 and '"error_code":30' in r.text:
                return True
            if r.status_code == 404 and '"error_code":29' in r.text:
                return False
        except: pass
        return False
