#!/usr/bin/env python3
"""Check internal links and anchors of the published site.

Usage: linkcheck.py [base-url]     (pages are fetched with curl)
"""
import glob
import os
import re
import subprocess
import sys
from urllib.parse import unquote, urldefrag, urljoin

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://pashapash.github.io/hmm3docs/"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
cache = {}


def get(url):
    if url not in cache:
        r = subprocess.run(["curl", "-s", "-L", "-w", "\n%{http_code}", url + "?x=" + str(os.getpid())],
                           capture_output=True)
        body, _, code = r.stdout.decode("utf-8", "replace").rpartition("\n")
        cache[url] = body if code == "200" else None
    return cache[url]


pages = [BASE]
for lang in ("en", "ru"):
    for f in sorted(glob.glob(os.path.join(ROOT, lang, "*.md"))):
        name = os.path.basename(f)[:-3]
        pages.append(BASE + lang + "/" + ("" if name == "index" else name + "/"))

checked = broken = 0
for page in pages:
    html = get(page)
    if html is None:
        print("MISSING PAGE", page)
        broken += 1
        continue
    main = html.split('<div id="main-content"', 1)[-1]
    for href in set(re.findall(r'href="([^"]+)"', main)):
        url, frag = urldefrag(urljoin(page, href))
        if not url.startswith(BASE):
            continue
        checked += 1
        target = get(url)
        if target is None:
            print("BROKEN", page, "->", href)
            broken += 1
        elif frag and ('id="%s"' % unquote(frag)) not in target:
            print("NO ANCHOR", page, "->", href)
            broken += 1
print("pages", len(pages), "links checked", checked, "broken", broken)
