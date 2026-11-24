"""Check every truthform command line on the site against a real binary.

Usage: python scripts/check-commands.py <path to a truthform binary built from core's main>

Each code block's `truthform <command> --flag ...` lines are matched against
that command's own `-h` output. A documented flag that does not exist reads
fine on the page and only fails when a customer runs it, which is how
release notes and docs usually go stale. Exits 1 if any flag is unknown, and
also if no command was found at all (the check must never pass by reading
nothing).
"""
import glob
import html
import re
import subprocess
import sys

# Parsed by main before the command's own flags, so `-h` does not list it.
GLOBAL_FLAGS = {"json"}

exe = sys.argv[1]
known = {}


def flags(cmd):
    if cmd not in known:
        # login takes its provider first, then its flags: "login -h" prints
        # only a usage line, which reads here as a command with no flags.
        # plan's flags belong to its subcommand ("plan rebuild"): "plan -h"
        # alone lists none, so every flag of a plan line would read as unknown.
        if cmd == "login":
            argv = [exe, cmd, "cloudflare", "-h"]
        elif cmd.startswith("plan "):
            argv = [exe, *cmd.split(), "-h"]
        else:
            argv = [exe, cmd, "-h"]
        out = subprocess.run(argv, capture_output=True, text=True)
        known[cmd] = set(re.findall(r"^\s+-([\w-]+)", out.stdout + out.stderr, re.M)) | GLOBAL_FLAGS
    return known[cmd]


bad = checked = 0
for page in sorted(glob.glob("public/**/*.html", recursive=True)):
    src = open(page, encoding="utf-8").read()
    for block in re.findall(r"<pre[^>]*>(.*?)</pre>", src, re.S):
        text = html.unescape(re.sub(r"<[^>]+>", "", block)).replace("\\\n", " ")
        for line in text.splitlines():
            m = re.match(r"(?:\$\s*)?truthform ([\w-]+)(.*)", line.strip())
            if not m:
                continue
            cmd, rest = m.groups()
            if cmd == "plan":
                sub, _, rest = rest.strip().partition(" ")
                cmd = f"plan {sub}"
            # Flags inside $(...) belong to another tool (az, gcloud), and
            # anything after a pipe to jq or grep.
            rest = re.sub(r"\$\([^)]*\)", "", rest.split("|")[0])
            checked += 1
            if cmd in ("mcp", "version"):
                continue
            for flag in re.findall(r"(?<![\w-])--([\w-]+)", rest):
                if flag not in flags(cmd):
                    bad += 1
                    print(f"{page}: truthform {cmd}: --{flag} is not a flag")

# Flags named in running text (<code>--zone-map ...</code>) are not tied to a
# command, so each must exist on at least one. Without this, a renamed flag
# that the page mentions only in prose passes unnoticed.
ANY = ["capture", "diff", "restore", "check", "permissions", "compare", "schema-diff", "report", "graph", "login",
       "translate", "skills", "plan rebuild", "plan secrets", "plan scope"]
everywhere = set().union(*(flags(c) for c in ANY))
for page in sorted(glob.glob("public/**/*.html", recursive=True)):
    src = re.sub(r"<pre[^>]*>.*?</pre>", "", open(page, encoding="utf-8").read(), flags=re.S)
    for code in re.findall(r"<code>(.*?)</code>", src, re.S):
        for flag in re.findall(r"(?<![\w-])--([\w-]+)", html.unescape(code)):
            checked += 1
            # The agents page explains argument passing as "--name=value".
            if flag not in everywhere and flag != "name":
                bad += 1
                print(f"{page}: --{flag} (in running text) is not a flag of any command")

print(f"{checked} command lines and flags checked, {bad} unknown")
if checked == 0 or bad:
    sys.exit(1)
