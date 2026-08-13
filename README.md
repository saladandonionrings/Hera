<div align="center">

# 🏛️ `hera`

<img width="100" height="150" alt="image" src="https://github.com/user-attachments/assets/7b5a41e3-5986-485d-a746-7a7e2b2a5f38" />


[![Python](https://img.shields.io/badge/Python-3.10%2B-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)

*Map the public digital footprint of an email address or username across dozens of platforms.*

</div>

> [!WARNING]
> this tool is designed strictly for personal digital footprint audits, security research, or explicitly authorized investigations. Only investigate targets for which you have received proper authorization.

## `modules`

| Category | Services / Tools |
| :--- | :--- |
| **identity/email** | Google Account (via [GHunt](https://github.com/mxrch/ghunt)), ProtonMail, Gravatar, WordPress |
| **phone** | Number validation, country/carrier/line-type lookup, WhatsApp & Telegram registration check |
| **dev platforms** | GitHub, GitLab, Bitbucket, npm, Docker Hub, HackerNews |
| **socials** | Snapchat, Facebook, multi-site username sweep (~40 sites via `blackbird`), [holehe](https://github.com/megadose/holehe) |
| **gaming/medias** | Steam, EA, Nexon, Chess.com, Lichess, Mojang/Minecraft, Roblox, Pokemon Showdown, Xbox Gamertag, stats.fm, Spotify, Duolingo, Vivino, Academia.edu, XVideos, Picsart, Imageshack, Smule |
| **creative/writing** | Trello, Wattpad |
| **isps** | French ISPs (Orange, SFR, Canal+) |
| **breaches** | Infostealer logs & breach intelligence via [Hudson Rock](https://www.hudsonrock.com/), breach names via [LeakCheck](https://leakcheck.io/) |

## `install`
```bash
git clone https://github.com/saladandonionrings/Hera
cd Hera
pip3 install -r requirements.txt
```

## `configuration`
> copy `.env.example` to `.env` and fill in your own values.

| Variable | Purpose | Required |
| :--- | :--- | :--- |
| `GITHUB_TOKEN` | Raises GitHub API rate limits | no |
| `KEYAPI_KEY` | [keyapi.ai](https://keyapi.ai) bearer token - more reliable Pinterest/Instagram profile lookups (avatar, name, bio, stats) than the built-in scraping fallback | no |
| `GOOGLE_CLIENT_ID` / `GOOGLE_PROJECT_ID` / `GOOGLE_CLIENT_SECRET` | Your own OAuth client for the Google profile-photo feature, create one at [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials) (type: Desktop app) | no* |
| `FACEBOOK_LSD_TOKEN` / `ESPN_API_KEY` | Override the built-in defaults if the platforms rotate them | no |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | Your own Telegram API app : create one at [my.telegram.org/apps](https://my.telegram.org/apps) | no** |

\* without the Google OAuth variables, identity lookup via GHunt **still works**; only the profile-photo fetch is skipped.

\*\* without `TELEGRAM_API_ID`/`TELEGRAM_API_HASH`, phone scans **still run**; only the Telegram check is skipped.

## `use`
### `cli`
```bash
# a email address
python3 main.py target@example.com

# a username
python3 main.py someusername

# a phone number
python3 main.py +33612345678

# usernames / emails / phone numbers from file
python3 main.py -f targets.txt
```

### `webapp`
```bash
python3 app.py
```
>-> http://localhost:8000

### `ghunt auth`
>the Google Identity module requires an authenticated **GHunt** session to operate correctly.

```bash
ghunt login
```

#### troubleshoot `ghunt` : `KeyError: 'container'`
```bash
python3 scripts/patch_ghunt.py
```

### `telegram auth` (optional, phone module)
>only needed once, to enable the Telegram registration check on phone number scans.

```bash
python3 scripts/telegram_login.py
```
