import sys
from colorama import init, Fore, Style

init(autoreset=True)

class OutputManager:
    def __init__(self, align_col=24):
        self.align_col = align_col
        
        # Palette Ultra-Moderne
        self.CYAN   = Fore.CYAN
        self.GREEN  = Fore.GREEN
        self.YELLOW = Fore.YELLOW
        self.RED    = Fore.RED
        self.GRAY   = "\033[90m"  # Gris foncé pour les libellés
        self.DIM    = Style.DIM
        self.BOLD   = Style.BRIGHT
        self.RESET  = Style.RESET_ALL

    def _format_line(self, icon, key, value, value_color=""):
        """Alignement chirurgical sans barres verticales."""
        # On ignore l'affichage si la valeur est nulle ou None
        if value is None or str(value).lower() in ["none", "", "null"]:
            return

        padding = max(1, self.align_col - len(str(key)))
        spaces = " " * padding
        
        # Structure : [ICÔNE] [KEY (Gris)] [ESPACES] [VALUE]
        print(f"  {icon}  {self.GRAY}{key}{self.RESET}{spaces}{value_color}{value}{self.RESET}")

    def main_header(self, title):
        """Bannière supérieure type 'Dashboard'."""
        line = "─" * 60
        print(f"\n {self.GRAY}{line}{self.RESET}")
        print(f"  {self.BOLD}{self.CYAN}TARGET {self.RESET}→ {self.BOLD}{title}{self.RESET}")
        print(f" {self.GRAY}{line}{self.RESET}")

    def module_header(self, title):
        """En-tête de module épuré avec soulignement fin."""
        print(f"\n  {self.BOLD}{self.CYAN}› {title.upper()}{self.RESET}")
        print(f"  {self.DIM}{'─' * 40}{self.RESET}")

    def info(self, key, value):
        self._format_line(f"{self.CYAN}•{self.RESET}", key, value)

    def success(self, key, value):
        self._format_line(f"{self.GREEN}✓{self.RESET}", key, value, self.GREEN)

    def warning(self, key, value):
        self._format_line(f"{self.YELLOW}!{self.RESET}", key, value, self.YELLOW)

    def error(self, key, value):
        self._format_line(f"{self.RED}×{self.RESET}", key, value, self.RED)

    def failure(self, key, value):
        """Discret pour ne pas polluer l'écran."""
        self._format_line(f"{self.DIM}○{self.RESET}", key, value, self.DIM)

    def sub_item(self, key, value):
        """Sous-élément avec indentation 'Soft'."""
        if value is None or str(value).lower() in ["none", ""]:
            return
        # Utilise un gris encore plus discret pour les sous-éléments
        padding = max(1, self.align_col - len(str(key)) - 4)
        spaces = " " * padding
        print(f"      {self.GRAY}└ {key}{self.RESET}{spaces}{self.DIM}{value}{self.RESET}")

console = OutputManager(align_col=24)