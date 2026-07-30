#!/usr/bin/env python3
"""
Correct bug GHunt (KeyError: 'container') 
Bug upstream (GHunt 2.3.4) :
    ghunt/parsers/people.py accède à
    cover_photo_data["metadata"]["container"
Usage :
    python3 scripts/patch_ghunt.py
"""
import shutil
import subprocess
import sys

BROKEN_LINE = 'self.coverPhotos[cover_photo_data["metadata"]["container"]] = person_cover_photo'
FIXED_LINE = 'self.coverPhotos[cover_photo_data.get("metadata", {}).get("container", "default")] = person_cover_photo'


def find_ghunt_python():
    ghunt_bin = shutil.which("ghunt")
    if not ghunt_bin:
        return None
    try:
        with open(ghunt_bin, "r", errors="ignore") as f:
            first_line = f.readline().strip()
    except OSError:
        return None
    if first_line.startswith("#!"):
        return first_line[2:].split()[0]
    return None


def find_people_parser_path(python_bin):
    try:
        result = subprocess.run(
            [python_bin, "-c", "import ghunt.parsers.people as p; print(p.__file__)"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception as e:
        print(f"[!] Could not execute : {python_bin} : {e}")
        return None
    if result.returncode != 0:
        print(f"[!] Could not find ghunt.parsers.people : {result.stderr.strip()}")
        return None
    return result.stdout.strip()


def patch_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if FIXED_LINE in content:
        print(f"[✓] Already corrected : {path}")
        return True
    if BROKEN_LINE not in content:
        print(f"[!] Line not found {path}.")
        print("    Your GHunt version is different than expected.")
        return False

    content = content.replace(BROKEN_LINE, FIXED_LINE)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✓] Correctif appliqué : {path}")
    return True


def main():
    python_bin = find_ghunt_python()
    if not python_bin:
        print("[!] `ghunt` not found.")
        sys.exit(1)

    people_path = find_people_parser_path(python_bin)
    if not people_path:
        sys.exit(1)

    sys.exit(0 if patch_file(people_path) else 1)


if __name__ == "__main__":
    main()
