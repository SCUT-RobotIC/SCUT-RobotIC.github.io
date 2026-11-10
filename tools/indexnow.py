# -*- coding: utf-8 -*-
"""Submit every page to IndexNow (Bing / Yandex / Seznam instant indexing).

The site hosts a key file named <KEY>.txt at the repository root; IndexNow
verifies ownership by fetching https://scut-robotic.github.io/<KEY>.txt.

Usage:  python tools/indexnow.py [--dry-run]
"""
import json
import os
import sys
import urllib.request

HOST = "scut-robotic.github.io"
KEY = "2fe03bd31099457d853263651e8c781c"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
PAGES = ["", "lab.html", "robots.html", "sponsor.html", "join.html"]
ENDPOINT = "https://api.indexnow.org/indexnow"


def main():
    urls = [f"https://{HOST}/{p}" for p in PAGES]
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }
    body = json.dumps(payload).encode("utf-8")

    if "--dry-run" in sys.argv:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow -> {resp.status} {resp.reason}")
    except urllib.error.HTTPError as exc:
        print(f"IndexNow -> HTTP {exc.code}: {exc.read().decode('utf-8', 'ignore')[:300]}")
    except Exception as exc:  # noqa: BLE001
        print(f"IndexNow -> failed: {exc}")
    print("submitted:", *urls, sep="\n  ")


if __name__ == "__main__":
    main()
