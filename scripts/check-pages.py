"""Check that every page under public/ carries the site's security policy.

Usage: python scripts/check-pages.py

GitHub Pages sends no custom headers, so each page holds its own
Content-Security-Policy in a meta tag. A page added without it, or with it
moved below the stylesheet, renders exactly the same and is simply
unprotected; nothing else would show it. The footer also promises no
analytics, which one pasted <script> would break just as quietly.

Exits 1 on any failure, and also if it found no pages (the check must never
pass by reading nothing).
"""
import glob
import re
import sys

POLICY = ("default-src 'none'; style-src 'self'; img-src 'self'; "
          "base-uri 'none'; form-action 'none'")

pages = sorted(glob.glob("public/**/*.html", recursive=True))
failures = []
for page in pages:
    with open(page, encoding="utf-8") as f:
        text = f.read()
    head = text.split("</head>", 1)[0]
    policies = re.findall(
        r'<meta http-equiv="Content-Security-Policy" content="([^"]*)">', head)
    if policies != [POLICY]:
        failures.append(f"{page}: policy is {policies or 'missing'}, want [{POLICY!r}]")
    else:
        # The policy covers only what follows it, so it must come before any
        # stylesheet, icon or image the head loads.
        before = head.split('http-equiv="Content-Security-Policy"', 1)[0]
        if re.search(r"<(link|img|style|script)\b", before):
            failures.append(f"{page}: something loads before the policy")
    if re.search(r"<script\b", text, re.I):
        failures.append(f"{page}: has a <script>; the footer promises no analytics")
    if '<meta name="referrer" content="no-referrer">' not in head:
        failures.append(f"{page}: no referrer policy")

if not pages:
    failures.append("no pages found under public/; run from the repo root")
for failure in failures:
    print(failure)
print(f"{len(pages)} pages checked, {len(failures)} failures")
sys.exit(1 if failures else 0)
