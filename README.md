# TruthForm website

Source for the public website at usetruthform.com. Hand-written HTML and CSS:
no framework, no build step, no JavaScript, no analytics, no third-party
requests. Each page loads at most three files, all from its own origin.

Every page uses root-absolute paths (`/styles.css`, `/docs/`), so a page
renders the same at any depth. The header, docs navigation and footer are
copied into each page by hand; there is no build step to share them, so a
change to one means the same change to all.

Only `public/` is served. Everything outside it (this README, `scripts/`)
stays out of the site: with the repo root as the output directory, this
README, with its deployment notes, would have been published at
`/README.md`.

| File (under `public/`) | Purpose |
| --- | --- |
| `index.html` | The home page |
| `docs/index.html` | Docs overview, linking the pages below |
| `docs/getting-started/index.html` | Install, credentials, the Cloudflare sign-in, capture, diff, restore (with `--dry-run` and `--subdomain`), environments, exit codes, `--json`, the Azure graph, known limits |
| `docs/rebuild/index.html` | Kubernetes rebuilds: `plan rebuild`, secret sources, scopes and holds, `--leave-out` and `--rename` into another environment |
| `docs/another-cloud/index.html` | `translate`: the map, what each service becomes, the audit evidence, workload identity, the GitOps report, the dry run, the skills |
| `docs/permissions/index.html` | What to grant per platform, each marked verified or expected as in core's `docs/permissions.md` |
| `docs/agents/index.html` | The MCP server (`truthform mcp`): tools, read-only rules, no restore tool |
| `styles.css` | All styling, shared by every page; light and dark mode via `prefers-color-scheme` |
| `logo.svg` | The mascot (a hermit crab holding the plumb bob, as on the GitHub org avatar), used as the footer mark and favicon; the header carries the same drawing inline |
| `404.html` | Not-found page; uses root-absolute paths so it renders at any depth |
| `robots.txt` | Allows all crawlers |

## Before going live

- **Every command line on the site must run.** Build `truthform` from core's
  `main` and run `python scripts/check-commands.py <path to truthform>`. It
  checks each `truthform` command and each `--flag` the pages name against the
  binary's own flags, and fails on any it does not know.
- Everything on the site is meant to be true of what is merged on core's
  `main`. When a roadmap item ships, move it to "What works today"; don't
  relabel it early. The docs are adapted from core's `docs/guide.md`,
  `docs/permissions.md` and `docs/architecture.md`; when those change, these
  pages need the same change.

## Preview locally

```sh
python -m http.server 8000 -d public
# open http://localhost:8000/
```

`http.server` shows its own error page for missing paths; open
`http://localhost:8000/404.html` to see ours. Check both colour schemes
(DevTools > Rendering > Emulate `prefers-color-scheme`) and a 360px-wide
viewport.

## Deploying

Pushing to `main` publishes `public/` to GitHub Pages through
`.github/workflows/pages.yml`. Pull requests run `scripts/check-pages.py`
only. After each deploy the workflow runs `scripts/check-live.py`, which
fetches the live site and fails unless the home page, docs index, stylesheet,
logo and 404 page are byte for byte this commit's. A deploy that finished
but is not what visitors get (DNS still at the parking page, a stale CDN
copy, the site served under `/site/`) fails the run instead of passing it.

Nothing is served outside `public/`: the workflow uploads that folder as the
Pages artifact. Pages' branch deploys can serve only the repo root or `/docs`,
and either would publish this README.

### Security headers

GitHub Pages sends no custom headers, so each page carries its
Content-Security-Policy and referrer policy in `<meta>` tags, right after the
charset (a meta policy covers only what follows it). `check-pages.py` fails a
page that lacks them, has them in the wrong place, or has any `<script>`.

Not covered by a meta tag, so not sent at all: `frame-ancestors` (browsers
ignore it in a meta policy), `X-Content-Type-Options` and `Permissions-Policy`.
The site has no forms, scripts or buttons that act on a click, so being
framed costs little. Moving hosting behind Cloudflare would bring them back
if that changes.

### First-time setup, once the repo is public

On the free plan GitHub serves Pages and enforces branch protection only for
public repositories. Before making it public, the history was checked for
client names and IDs, personal paths, account IDs and secrets (all refs,
every blob, every commit message, every PR's text and comments) on
2026-11-27, and was clean. The commit author addresses become public with it.

1. `gh repo edit UseTruthForm/site --visibility public --accept-visibility-change-consequences`
2. Org Settings > Pages > Add a domain: `usetruthform.com`. GitHub gives a TXT
   record (`_github-pages-challenge-usetruthform`); add it in the Cloudflare
   zone (DNS only) and press Verify. This stops any other GitHub account pointing a Pages site at
   the domain.
3. DNS in Cloudflare (all three domains' nameservers moved there on
   2026-11-27). Adding a zone copies the registrar's records, including its
   parking records (`@` to a Namecheap redirect server, `www CNAME
   parkingpage.namecheap.com`), proxied. Proxied to a server with no HTTPS,
   the apex answered **522** and `www` served the registrar's "for sale"
   page. Delete those two, keep the MX and SPF records (mail forwarding), and
   add these, all **DNS only (grey cloud)**:

   | Type | Host | Value |
   | --- | --- | --- |
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153` |
   | AAAA | `@` | `2606:50c0:8001::153` |
   | AAAA | `@` | `2606:50c0:8002::153` |
   | AAAA | `@` | `2606:50c0:8003::153` |
   | CNAME | `www` | `usetruthform.github.io.` |

   The `www` target is the org's Pages host, `usetruthform.github.io`. An
   earlier version of this README said `truthform.github.io`, which belongs
   to whoever owns that name and would have pointed `www` at their site.

   DNS only, not proxied: GitHub issues the certificate only when the names
   resolve to its own addresses, and a proxied record hides them. Proxying
   with SSL mode "Flexible" would also loop, since Pages redirects HTTP to
   HTTPS once HTTPS is enforced.
4. `scripts/configure-repo.sh`: sets Pages to deploy from the workflow, the
   custom domain, HTTPS, and protection on `main` (pull requests only, the
   `check` job must pass, no force pushes or deletion, admins included). It
   reads each setting back. HTTPS cannot be enforced until GitHub has issued
   the certificate, which follows DNS by minutes to an hour; the script says
   so, and rerunning it later enforces it. If the certificate stays
   `null` with DNS correct, clear the domain and set it again
   (`gh api -X PUT repos/UseTruthForm/site/pages -F cname=null`, then rerun
   the script); that started it on 2026-11-27.
5. Actions > Pages > Run workflow (or push to `main`), and check that the
   "Check the live site" step passes.

GitHub redirects `www` to the apex itself once both resolve.

### truthform.org and truthform.dev -> usetruthform.com

Both zones are in Cloudflare. Each has one Single Redirect rule: host is the
domain or its `www`, 301 to `concat("https://usetruthform.com",
http.request.uri.path)`, query string kept. The rule runs only on proxied
traffic, so `@` and `www` are **proxied** A records to `192.0.2.1`, an
address reserved for documentation that serves nothing; Cloudflare answers
every request with the redirect before it would be forwarded. The MX and SPF
records stay. `.dev` is HTTPS-only in browsers, which Cloudflare's own
certificate covers.

### Checking by hand

`python scripts/check-live.py https://usetruthform.com/ public` is the same
check the workflow runs. These cover what it does not:

```sh
curl -sI https://www.usetruthform.com/ | grep -i '^location'         # expect https://usetruthform.com/
curl -sI http://usetruthform.com/ | grep -i '^location'              # expect https://usetruthform.com/ once HTTPS is enforced
curl -sI https://truthform.org/x | grep -iE '^(HTTP|location)'       # expect 301 to https://usetruthform.com/x
curl -sI https://truthform.dev/x | grep -iE '^(HTTP|location)'       # expect 301 to https://usetruthform.com/x
```
