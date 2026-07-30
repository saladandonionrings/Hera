import os
import sys
import io
import json
import asyncio
import re
import subprocess
import threading
import queue
import uuid
from flask import Flask, render_template, request, jsonify, Response

from main import EpeiosPro

app = Flask(__name__)

# Pending Telegram logins, keyed by a one-time token: token -> {api_id, api_hash, phone, phone_code_hash}
_telegram_login_sessions = {}

def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def _ensure_event_loop():
    """Flask's dev server handles each request in its own worker thread, but
    asyncio only auto-creates a loop on the main thread - Telethon's sync
    wrapper needs one to exist in whichever thread it runs in."""
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

def _persist_telegram_credentials(api_id, api_hash):
    """Writes TELEGRAM_API_ID/TELEGRAM_API_HASH to .env so modules/phone.py
    picks them up immediately (it re-reads .env on every scan) and so they
    survive a server restart, without requiring a manual .env edit."""
    from dotenv import set_key
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(dotenv_path):
        open(dotenv_path, "a").close()
    set_key(dotenv_path, "TELEGRAM_API_ID", api_id)
    set_key(dotenv_path, "TELEGRAM_API_HASH", api_hash)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ghunt-login', methods=['POST'])
def ghunt_login():
    """auth GHunt non-interactively using a base64 cookie"""
    payload = request.get_json(silent=True) or {}
    cookies_b64 = (payload.get('cookies_b64') or '').strip()

    if not cookies_b64:
        return jsonify({"error": "No cookies provided."}), 400

    try:
        subprocess.run(["ghunt", "login", "--clean"], capture_output=True, text=True, timeout=15)

        process = subprocess.run(
            ["ghunt", "login"],
            input=f"2\n{cookies_b64}\n",
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = clean_ansi(f"{process.stdout}\n{process.stderr}").strip()
        success = "Cookies and osids generated" in output

        return jsonify({"success": success, "output": output})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "ghunt login timed out."}), 504
    except FileNotFoundError:
        return jsonify({"error": "`ghunt` command not found on the server."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/telegram-login/start', methods=['POST'])
def telegram_login_start():
    """Step 1: connect with the user's own Telegram API app and request a login code."""
    payload = request.get_json(silent=True) or {}
    api_id = (payload.get('api_id') or '').strip()
    api_hash = (payload.get('api_hash') or '').strip()
    phone = (payload.get('phone') or '').strip()

    if not (api_id and api_hash and phone):
        return jsonify({"error": "API ID, API Hash and phone number are all required."}), 400
    if not api_id.isdigit():
        return jsonify({"error": "API ID must be numeric."}), 400

    try:
        from telethon.sync import TelegramClient
    except ImportError:
        return jsonify({"error": "telethon not installed on the server (pip install telethon)."}), 500

    session_name = os.getenv("TELEGRAM_SESSION", "hera_telegram")
    _ensure_event_loop()

    client = None
    try:
        client = TelegramClient(session_name, int(api_id), api_hash)
        client.connect()

        if client.is_user_authorized():
            me = client.get_me()
            _persist_telegram_credentials(api_id, api_hash)
            return jsonify({"success": True, "message": f"Already authenticated as {me.first_name}."})

        sent = client.send_code_request(phone)
        token = uuid.uuid4().hex
        # Only the phone_code_hash needs to survive to the next request - the
        # client connection itself doesn't (and can't safely be kept alive
        # across requests, which may land on different worker threads).
        _telegram_login_sessions[token] = {
            "api_id": api_id,
            "api_hash": api_hash,
            "phone": phone,
            "phone_code_hash": sent.phone_code_hash,
        }
        return jsonify({"success": True, "token": token, "message": "Code sent - check your Telegram app."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if client is not None:
            client.disconnect()

@app.route('/telegram-login/verify', methods=['POST'])
def telegram_login_verify():
    """Step 2: complete the login with the received code, and the 2FA password if Telegram asks for one."""
    payload = request.get_json(silent=True) or {}
    token = (payload.get('token') or '').strip()
    code = (payload.get('code') or '').strip()
    password = payload.get('password') or ''

    pending = _telegram_login_sessions.get(token)
    if not pending:
        return jsonify({"error": "No pending login for this token - send a code first."}), 400
    if not code:
        return jsonify({"error": "Code is required."}), 400

    try:
        from telethon.sync import TelegramClient
        from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
    except ImportError:
        return jsonify({"error": "telethon not installed on the server (pip install telethon)."}), 500

    session_name = os.getenv("TELEGRAM_SESSION", "hera_telegram")
    _ensure_event_loop()

    # Reconnect fresh rather than reusing a client kept alive from /start -
    # that request may have run on a different worker thread. The same
    # session file + the saved phone_code_hash is enough to finish the login.
    client = None
    try:
        client = TelegramClient(session_name, int(pending["api_id"]), pending["api_hash"])
        client.connect()

        try:
            client.sign_in(pending["phone"], code, phone_code_hash=pending["phone_code_hash"])
        except SessionPasswordNeededError:
            if not password:
                return jsonify({"success": True, "needs_password": True, "message": "2FA is enabled - enter your Telegram password and verify again."})
            client.sign_in(password=password)

        me = client.get_me()
        _persist_telegram_credentials(pending["api_id"], pending["api_hash"])
        del _telegram_login_sessions[token]
        return jsonify({"success": True, "message": f"Authenticated as {me.first_name}. Session saved for future scans."})
    except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if client is not None:
            client.disconnect()

@app.route('/scan', methods=['POST'])
def start_investigation():
    payload = request.get_json(silent=True) or {}
    target = (payload.get('target') or '').strip()

    if not target:
        return jsonify({"error": "No target given."}), 400

    output_capture = io.StringIO()
    sys.stdout = output_capture

    try:
        epeios = EpeiosPro(target)
        asyncio.run(epeios.scan())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sys.stdout = sys.__stdout__

    return jsonify({
        "raw_logs": clean_ansi(output_capture.getvalue())
    })

@app.route('/scan-stream')
def scan_stream():
    """Same scan as /scan, but streamed to the client as it runs (SSE) so the
    UI can render results as soon as each module prints them, instead of
    waiting for the entire multi-module scan to finish."""
    target = (request.args.get('target') or '').strip()

    if not target:
        return jsonify({"error": "No target given."}), 400

    def generate():
        output_queue = queue.Queue()

        class QueueWriter:
            def write(self, s):
                if s:
                    output_queue.put(s)
            def flush(self):
                pass

        error_holder = {}

        def run_scan():
            old_stdout = sys.stdout
            sys.stdout = QueueWriter()
            try:
                epeios = EpeiosPro(target)
                asyncio.run(epeios.scan())
            except Exception as e:
                error_holder['error'] = str(e)
            finally:
                sys.stdout = old_stdout
                output_queue.put(None)

        threading.Thread(target=run_scan, daemon=True).start()

        buffer = ""
        done = False
        while not done:
            chunk = output_queue.get()  # blocks until the next write, or the sentinel
            if chunk is None:
                break
            buffer += chunk
            # Drain anything else already queued so a burst of prints from the
            # same module becomes one update instead of many tiny ones.
            while True:
                try:
                    more = output_queue.get_nowait()
                except queue.Empty:
                    break
                if more is None:
                    done = True
                    break
                buffer += more
            yield f"data: {json.dumps({'raw_logs': clean_ansi(buffer)})}\n\n"

        if 'error' in error_holder:
            yield f"event: scan_error\ndata: {json.dumps({'error': error_holder['error']})}\n\n"
        else:
            yield f"event: done\ndata: {json.dumps({'raw_logs': clean_ansi(buffer)})}\n\n"

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive',
    })

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, port=8000, threaded=True)
