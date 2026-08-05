import os

import phonenumbers
import requests
from phonenumbers import carrier as pn_carrier
from phonenumbers import geocoder, timezone as pn_timezone
from dotenv import load_dotenv

from core.display import console

load_dotenv()

TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION", "hera_telegram")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

LINE_TYPES = {
    phonenumbers.PhoneNumberType.MOBILE: "Mobile",
    phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
    phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed/Mobile",
    phonenumbers.PhoneNumberType.VOIP: "VoIP",
    phonenumbers.PhoneNumberType.TOLL_FREE: "Toll Free",
    phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
    phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal",
    phonenumbers.PhoneNumberType.PAGER: "Pager",
    phonenumbers.PhoneNumberType.UAN: "UAN",
    phonenumbers.PhoneNumberType.UNKNOWN: "Unknown",
}


class PhoneScanner:
    """Phone number OSINT: validation, carrier/region lookup, WhatsApp + Telegram presence."""

    def __init__(self, raw_number):
        self.raw_number = raw_number.strip()
        self.parsed = None
        self.e164 = ""

    def _parse(self):
        region = None if self.raw_number.startswith("+") else "FR"
        try:
            self.parsed = phonenumbers.parse(self.raw_number, region)
        except phonenumbers.NumberParseException as e:
            console.error("Phone Parse", str(e))
            return False
        if not phonenumbers.is_valid_number(self.parsed):
            return False
        self.e164 = phonenumbers.format_number(self.parsed, phonenumbers.PhoneNumberFormat.E164)
        return True

    def scan(self):
        console.module_header("PHONE NUMBER")

        if not self._parse():
            console.failure("Phone Number", "Invalid or unparsable number.")
            return False

        console.success("Valid Number", self.e164)
        console.info("International", phonenumbers.format_number(self.parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL))
        console.info("National", phonenumbers.format_number(self.parsed, phonenumbers.PhoneNumberFormat.NATIONAL))

        region = geocoder.description_for_number(self.parsed, "en")
        if region:
            console.info("Region", region)

        operator = pn_carrier.name_for_number(self.parsed, "en")
        if operator:
            console.info("Carrier", operator)

        timezones = pn_timezone.time_zones_for_number(self.parsed)
        if timezones:
            console.info("Timezone", ", ".join(timezones))

        line_type = LINE_TYPES.get(phonenumbers.number_type(self.parsed), "Unknown")
        console.info("Line Type", line_type)

        self._check_whatsapp()
        self._check_telegram()
        return True

    def _check_whatsapp(self):
        """Uses WhatsApp's own public click-to-chat page: it renders an
        'invalid number' message for numbers that aren't registered, and a
        chat-redirect page for numbers that are — no message is sent."""
        try:
            number = self.e164.replace("+", "")
            resp = requests.get(
                f"https://api.whatsapp.com/send?phone={number}",
                headers={"User-Agent": USER_AGENT},
                timeout=10,
            )
            text = resp.text.lower()
            invalid_markers = ["phone number shared via url is invalid", "numéro de téléphone", "url is invalid"]
            if resp.status_code == 200 and not any(m in text for m in invalid_markers):
                console.success("WhatsApp", "Registered")
            elif resp.status_code == 200:
                console.failure("WhatsApp", "Not registered.")
            else:
                console.warning("WhatsApp", "Could not determine status.")
        except Exception as e:
            console.warning("WhatsApp", f"Check failed ({str(e)[:60]}).")

    def _check_telegram(self):
        """Optional: requires the user's own Telegram API credentials and a
        pre-authenticated session (see scripts/telegram_login.py, or the
        Telegram section of the credentials drawer in the web app). Re-reads
        .env on every call (rather than caching at import time) so a login
        done via the web app takes effect immediately, without restarting
        the server. Skips gracefully when not configured."""
        load_dotenv(override=True)
        telegram_api_id = os.getenv("TELEGRAM_API_ID")
        telegram_api_hash = os.getenv("TELEGRAM_API_HASH")

        if not (telegram_api_id and telegram_api_hash):
            console.warning("Telegram", "Skipped - set TELEGRAM_API_ID/TELEGRAM_API_HASH in .env to enable.")
            return

        try:
            from telethon.sync import TelegramClient
            from telethon.tl.functions.contacts import DeleteContactsRequest, ImportContactsRequest
            from telethon.tl.types import InputPhoneContact
        except ImportError:
            console.warning("Telegram", "telethon not installed (pip install telethon).")
            return

        if not os.path.exists(f"{TELEGRAM_SESSION}.session"):
            console.warning("Telegram", "No session yet - authenticate via the credentials drawer or run `python3 scripts/telegram_login.py`.")
            return

        try:
            with TelegramClient(TELEGRAM_SESSION, int(telegram_api_id), telegram_api_hash) as client:
                if not client.is_user_authorized():
                    console.warning("Telegram", "Session expired - run `python3 scripts/telegram_login.py` again.")
                    return

                contact = InputPhoneContact(client_id=0, phone=self.e164, first_name="Hera", last_name="Scan")
                result = client(ImportContactsRequest([contact]))

                if result.users:
                    user = result.users[0]
                    console.success("Telegram", "Registered")
                    if user.username:
                        console.info("Telegram Username", f"@{user.username}")
                    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                    if full_name:
                        console.info("Telegram Name", full_name)
                    try:
                        client(DeleteContactsRequest(id=[user.id]))
                    except Exception:
                        pass
                else:
                    console.failure("Telegram", "Not registered.")
        except Exception as e:
            console.warning("Telegram", f"Check failed ({str(e)[:60]}).")
