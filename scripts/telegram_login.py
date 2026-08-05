#!/usr/bin/env python3
"""
Authentifie une session Telethon une bonne fois pour toutes, pour permettre
au module Phone Number de Hera (modules/phone.py) de vérifier si un numéro
est enregistré sur Telegram.

Prérequis : TELEGRAM_API_ID et TELEGRAM_API_HASH dans .env
(à obtenir sur https://my.telegram.org/apps).

Ce script demande votre propre numéro de téléphone, puis le code de
confirmation envoyé par Telegram, et enregistre la session dans
hera_telegram.session (ou TELEGRAM_SESSION si défini). Il ne doit être
lancé qu'une fois - Hera réutilisera ensuite cette session automatiquement.

Usage :
    python3 scripts/telegram_login.py
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = os.getenv("TELEGRAM_SESSION", "hera_telegram")


def main():
    if not (API_ID and API_HASH):
        print("[!] TELEGRAM_API_ID / TELEGRAM_API_HASH manquants dans .env.")
        print("    Créez vos identifiants sur https://my.telegram.org/apps")
        sys.exit(1)

    try:
        from telethon.sync import TelegramClient
    except ImportError:
        print("[!] telethon n'est pas installé (pip install telethon).")
        sys.exit(1)

    with TelegramClient(SESSION_NAME, int(API_ID), API_HASH) as client:
        me = client.get_me()
        print(f"[✓] Session Telegram active : {SESSION_NAME}.session (connecté en tant que {me.first_name}).")


if __name__ == "__main__":
    main()
