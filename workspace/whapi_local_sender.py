#!/usr/bin/env python3
"""
Standalone WHAPI sender for WhatsApp text + files.
No Hermes dependency. Run locally or on VPS.

Setup:
  cd /home/mohit/workspace
  python3 -m pip install requests python-dotenv

.env required:
  WHAPI_TOKEN=your_whapi_token_here
  WHATSAPP_GROUP=120363426619711887@g.us

Usage:
  python3 whapi_local_sender.py text "hello admin group"
  python3 whapi_local_sender.py file /absolute/path/report.pdf "Report caption"
  python3 whapi_local_sender.py image /absolute/path/chart.png "Chart caption"
  python3 whapi_local_sender.py status
"""

import argparse
import base64
import mimetypes
import os
import sys
import time
from pathlib import Path

import requests
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

WHAPI_BASE = "https://gate.whapi.cloud"
DEFAULT_GROUP = "120363426619711887@g.us"


def load_config():
    env_path = Path(__file__).with_name(".env")
    if load_dotenv and env_path.exists():
        load_dotenv(env_path)

    token = os.getenv("WHAPI_TOKEN", "").strip()
    default_to = os.getenv("WHATSAPP_GROUP", DEFAULT_GROUP).strip()

    if not token:
        raise SystemExit(
            "ERROR: WHAPI_TOKEN missing. Add it to /home/mohit/workspace/.env\n"
            "Example:\nWHAPI_TOKEN=xxxxxxxx\nWHATSAPP_GROUP=120363426619711887@g.us"
        )
    return token, default_to


def request_whapi(method, path, token, payload=None, retries=3, timeout=60):
    url = f"{WHAPI_BASE}{path}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
    }

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(method, url, headers=headers, json=payload, timeout=timeout)
            text = resp.text
            if 200 <= resp.status_code < 300:
                return True, resp.status_code, text
            last_error = f"HTTP {resp.status_code}: {text}"
        except Exception as e:
            last_error = repr(e)

        if attempt < retries:
            time.sleep(2 * attempt)

    return False, 0, last_error


def send_text(token, to, body):
    return request_whapi("POST", "/messages/text", token, {"to": to, "body": body}, timeout=30)


def media_endpoint(media_type, file_path):
    if media_type:
        media_type = media_type.lower().strip()
    if media_type in {"image", "video", "audio", "document"}:
        return f"/messages/{media_type}"

    mime, _ = mimetypes.guess_type(str(file_path))
    if mime:
        if mime.startswith("image/"):
            return "/messages/image"
        if mime.startswith("video/"):
            return "/messages/video"
        if mime.startswith("audio/"):
            return "/messages/audio"
    return "/messages/document"


def send_file(token, to, file_path, caption="", media_type=None):
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"ERROR: file not found: {path}")

    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        mime = "application/octet-stream"

    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    media_payload = f"data:{mime};name={path.name};base64,{b64}"
    payload = {"to": to, "media": media_payload}
    if caption:
        payload["caption"] = caption

    return request_whapi("POST", media_endpoint(media_type, path), token, payload, timeout=120)


def status(token):
    return request_whapi("GET", "/health", token, None, timeout=30)


def main():
    parser = argparse.ArgumentParser(description="Standalone WHAPI WhatsApp sender")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_text = sub.add_parser("text")
    p_text.add_argument("body")
    p_text.add_argument("--to", default=None)

    p_file = sub.add_parser("file")
    p_file.add_argument("path")
    p_file.add_argument("caption", nargs="?", default="")
    p_file.add_argument("--to", default=None)
    p_file.add_argument("--type", choices=["document", "image", "video", "audio"], default="document")

    p_image = sub.add_parser("image")
    p_image.add_argument("path")
    p_image.add_argument("caption", nargs="?", default="")
    p_image.add_argument("--to", default=None)

    p_status = sub.add_parser("status")

    args = parser.parse_args()
    token, default_to = load_config()
    to = getattr(args, "to", None) or default_to

    if args.cmd == "text":
        ok, code, out = send_text(token, to, args.body)
    elif args.cmd == "file":
        ok, code, out = send_file(token, to, args.path, args.caption, args.type)
    elif args.cmd == "image":
        ok, code, out = send_file(token, to, args.path, args.caption, "image")
    elif args.cmd == "status":
        ok, code, out = status(token)
    else:
        raise SystemExit("unknown command")

    print("SUCCESS" if ok else "FAILED")
    if code:
        print(f"HTTP_STATUS={code}")
    print(out)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
