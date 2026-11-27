#!/usr/bin/env bash
# Apply the repo settings GitHub keeps outside the repo: Pages served from the
# workflow, the custom domain, HTTPS, and protection on main. Safe to rerun;
# each step sets the value whether or not it is already set.
#
# Usage: scripts/configure-repo.sh   (needs gh signed in as an org admin)
#
# Both need the repo public: on the free plan GitHub refuses Pages and
# branch protection for private repos (404 and 403), so the script stops
# rather than half-apply.
set -euo pipefail

repo=UseTruthForm/site
domain=usetruthform.com

visibility=$(gh api "repos/$repo" --jq .visibility)
if [ "$visibility" != public ]; then
  echo "$repo is $visibility; make it public first" >&2
  exit 1
fi

# Pages from the workflow, not from a branch: a branch deploy can serve only
# the root or /docs, and either would publish the README.
if gh api "repos/$repo/pages" >/dev/null 2>&1; then
  gh api -X PUT "repos/$repo/pages" -f build_type=workflow >/dev/null
else
  gh api -X POST "repos/$repo/pages" -f build_type=workflow >/dev/null
fi
gh api -X PUT "repos/$repo/pages" -f cname="$domain" >/dev/null

# GitHub refuses this until it has issued the certificate, which needs DNS
# pointing at it first. Say so rather than fail: rerun once DNS is in.
if gh api -X PUT "repos/$repo/pages" -F https_enforced=true >/dev/null 2>&1; then
  echo "HTTPS enforced"
else
  echo "HTTPS not enforced yet: certificate not issued; rerun once DNS points at Pages"
fi

# main takes changes only through a pull request whose check passed, and
# cannot be force-pushed or deleted. enforce_admins is on because every
# maintainer is an admin: off, the rule would bind nobody. No approving
# review is required, since a lone maintainer cannot approve their own PR.
gh api -X PUT "repos/$repo/branches/main/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": { "strict": false, "contexts": ["check"] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

# Read everything back: a setting that did not take reads the same as one
# that did until something goes wrong.
gh api "repos/$repo/pages" --jq '"pages: build=\(.build_type) cname=\(.cname) https=\(.https_enforced) url=\(.html_url)"'
gh api "repos/$repo/branches/main/protection" --jq '"main: checks=\(.required_status_checks.contexts) admins=\(.enforce_admins.enabled) force_push=\(.allow_force_pushes.enabled) deletions=\(.allow_deletions.enabled)"'
