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
| `_headers` | Response headers on Cloudflare Pages: a Content-Security-Policy allowing only the site's own stylesheet and images, and `noindex` on `*.pages.dev` |

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

Nothing is deployed yet. GitHub Pages on the free org plan only serves
**public** repositories, and this one is private, so there are two options.

### Recommended: (b) Cloudflare Pages, repo stays private

usetruthform.com is not on Cloudflare nameservers yet (it is on the registrar's
default DNS); move it first. Then DNS, TLS and hosting end up in one place, nothing needs to become public, and every pushed branch gets its
own preview URL, so a pull request can be reviewed as a rendered site
before merging. The cost is one more integration: the Cloudflare Pages GitHub
app needs read access to this repo.

1. Cloudflare dashboard > Workers & Pages > Create > Pages > Connect to Git.
   Install the Cloudflare Pages GitHub app on the UseTruthForm org and grant it
   **only** `UseTruthForm/site`.
2. Project settings:
   - Production branch: `main`
   - Framework preset: None
   - Build command: *(leave empty)*
   - Build output directory: `public`
3. Deploy, then open the `*.pages.dev` URL and check the page (not just the
   status code).
4. Project > Custom domains > add `usetruthform.com`, then `www.usetruthform.com`.
   Because the zone is on Cloudflare, it creates the proxied DNS records
   itself (a flattened CNAME at the apex to `<project>.pages.dev`). Remove any
   older A/AAAA/CNAME records for those names first, or the add fails.
5. Redirect `www` to the apex: Rules > Redirect Rules > create rule,
   hostname equals `www.usetruthform.com`, dynamic redirect to
   `concat("https://usetruthform.com", http.request.uri.path)`, status 301,
   preserve query string.

Note: preview deployments are reachable by anyone who has the URL. Put
Cloudflare Access in front of previews if that matters.

### Alternative: (a) GitHub Pages, repo made public

Simplest if publishing the site source is fine. It makes the whole repo
history public.

1. `gh repo edit UseTruthForm/site --visibility public --accept-visibility-change-consequences`
2. Settings > Pages > Build and deployment > Source: GitHub Actions, with a
   workflow that uploads `public/` (`actions/upload-pages-artifact` with
   `path: public`, then `actions/deploy-pages`). Branch deploys serve only
   the repo root or `/docs`, and either would publish this README. Custom
   domain: `usetruthform.com`.
3. Org Settings > Pages > add and verify `usetruthform.com` (a TXT record), so
   nobody else can point a Pages site at the domain.
4. DNS in Cloudflare, all **DNS only (grey cloud)** until GitHub has issued the
   certificate; proxying hides the origin from GitHub's certificate check:

   | Type | Name | Content |
   | --- | --- | --- |
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153` |
   | AAAA | `@` | `2606:50c0:8001::153` |
   | AAAA | `@` | `2606:50c0:8002::153` |
   | AAAA | `@` | `2606:50c0:8003::153` |
   | CNAME | `www` | `truthform.github.io` |

   Instead of the eight apex records, a single `CNAME @ truthform.github.io`
   also works, because Cloudflare flattens CNAMEs at the apex.
5. Once the certificate shows as issued, tick Enforce HTTPS. GitHub redirects
   `www` to the apex itself.

### truthform.org -> usetruthform.com

truthform.org's DNS is at Namecheap.

- **Recommended:** add truthform.org as a zone in Cloudflare (free plan) and
  switch its nameservers at Namecheap to the two Cloudflare gives you. Then
  add proxied (orange cloud) placeholder records so requests reach
  Cloudflare: `A @ 192.0.2.1` and `A www 192.0.2.1`. Add a Redirect Rule:
  hostname is in {`truthform.org`, `www.truthform.org`}, dynamic redirect to
  `concat("https://usetruthform.com", http.request.uri.path)`, 301, preserve
  query string. This serves the redirect over HTTPS with Cloudflare's
  certificate.
- **Without moving DNS:** Namecheap > Domain List > truthform.org > Advanced
  DNS > add "URL Redirect Record" for `@` and `www` to
  `https://usetruthform.com/`, Permanent (301). Check that
  `https://truthform.org` (not only `http://`) redirects before relying on it.

### After deploying, check it really works

```sh
curl -s https://usetruthform.com/ | grep -c "Capture what you run"   # expect 1
curl -sI https://www.usetruthform.com/ | grep -i '^location'         # expect https://usetruthform.com/
curl -s -o /dev/null -w '%{http_code}\n' https://usetruthform.com/nope # expect 404, not 200
curl -sI https://truthform.org/x | grep -iE '^(HTTP|location)'       # expect 301 to https://usetruthform.com/x
curl -sI https://usetruthform.com/ | grep -ic '^content-security-policy: default-src' # expect 1: _headers applied
curl -sI https://<project>.pages.dev/ | grep -i '^x-robots-tag'      # expect noindex
curl -sI https://usetruthform.com/ | grep -ic '^set-cookie'               # expect 0: the footer says no cookies
curl -s https://usetruthform.com/ | grep -ic '<script'                  # expect 0: the footer says no analytics
```

A `200` for `/nope` means the host is falling back to `index.html` for missing
pages and `404.html` was not picked up.

A missing `content-security-policy` means `_headers` was not picked up (it
must sit at the build output root). The pages still render without it, so
nothing else would show the protection is absent.

The footer promises no cookies and no analytics, and Cloudflare can break both
without any change here: Bot Fight Mode on the zone sets a `__cf_bm` cookie,
and Pages' Web Analytics setting injects a beacon script into every page (the
CSP then blocks it, which hides it further). Keep both off; the two checks
above catch either being turned on.
