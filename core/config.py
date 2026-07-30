import re

import phonenumbers

# Liste des domaines reconnus comme étant gérés par ProtonMail
PROTON_DOMAINS = [
    "proton.me",
    "protonmail.com",
    "pm.me",
    "protonmail.ch",
    "passmail.net"
]

def is_valid_email(target):
    """
    Vérifie si la cible fournie est une adresse email (True) ou un pseudo (False).
    """
    return re.match(r"[^@]+@[^@]+\.[^@]+", target) is not None

def is_valid_phone(target):
    """
    Vérifie si la cible fournie est un numéro de téléphone (True) plutôt qu'un
    email/pseudo. Un numéro sans '+' est interprété par défaut en France.
    """
    candidate = target.strip()
    if not re.match(r"^\+?[\d\s\-\.\(\)]{6,}$", candidate):
        return False
    try:
        region = None if candidate.startswith("+") else "FR"
        parsed = phonenumbers.parse(candidate, region)
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False