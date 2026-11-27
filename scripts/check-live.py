"""Check that a deployed site serves exactly this checkout's public/ folder.

Usage: python scripts/check-live.py <site URL> <public dir>

Run by the Pages workflow after each deploy, and safe to run by hand. Status
codes alone prove nothing here: the registrar's parking page and a stale CDN
copy both answer 200. So each check compares the bytes served with the bytes
in the checkout. Retries for a few minutes, because the CDN takes a while to
pick up a new deploy; exits 1 if the site still does not match.
"""
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

site, public = sys.argv[1].rstrip("/") + "/", sys.argv[2]


def fetch(path):
    # A query string the CDN has not seen, so the answer is not a cached
    # copy from before this deploy.
    url = urllib.parse.urljoin(site, path) + f"?check={time.time_ns()}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.status, r.read(), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers
    except (urllib.error.URLError, OSError) as e:
        # Before DNS points at Pages, or while the certificate is issued,
        # the host may not answer at all. That is a difference to retry and
        # report, not a crash.
        return f"unreachable ({e})", b"", {}


def local(name):
    with open(os.path.join(public, name), "rb") as f:
        return f.read()


def problems():
    found = []
    # Every page links /styles.css and /docs/ from the root, so a site served
    # under a path (usetruthform.github.io/site/, before the custom domain is
    # set) renders unstyled with broken links.
    if urllib.parse.urlparse(site).path != "/":
        return [f"{site} is not at the root of its host; set the custom domain"]
    for path, name in [("", "index.html"), ("docs/", "docs/index.html"),
                       ("styles.css", "styles.css"), ("logo.svg", "logo.svg")]:
        status, body, headers = fetch(path)
        if status != 200 or body != local(name):
            found.append(f"/{path}: {status}, {len(body)} bytes, not public/{name}")
        if headers.get("Set-Cookie"):
            found.append(f"/{path}: sets a cookie; the footer promises none")
    # A missing page must be a real 404 showing our page. A 200 here means
    # the host falls back to index.html, and search engines index the error.
    status, body, _ = fetch("no-such-page/")
    if status != 404 or body != local("404.html"):
        found.append(f"/no-such-page/: {status}, not public/404.html with a 404")
    # Only public/ is meant to be served. The README holds deployment notes.
    status, _, _ = fetch("README.md")
    if status != 404:
        found.append(f"/README.md: {status}; only public/ should be served")
    return found


deadline = time.time() + int(os.environ.get("CHECK_LIVE_WAIT", "300"))
while True:
    found = problems()
    if not found or time.time() >= deadline:
        break
    print(f"not live yet ({len(found)} differences), retrying in 15s")
    time.sleep(15)
for line in found:
    print(line)
print(f"{site}: {'matches this checkout' if not found else 'does NOT match'}")
sys.exit(1 if found else 0)
