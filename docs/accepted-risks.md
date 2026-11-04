# Accepted dependency risks

This file records every dependency vulnerability (CRITICAL or HIGH) that is
knowingly shipped, with a justification and a review date. Anything not
listed here must be fixed before deployment.

Dependency versions are pinned exactly in `backend/requirements.txt` and
`frontend/package.json`. Dependabot (`.github/dependabot.yml`) opens weekly
update PRs for pip, npm, the backend Docker base image and GitHub Actions.

## Remediated (2026-11-04)

| Package | From | To | Advisories addressed |
|---|---|---|---|
| Django | 5.0.9 (EOL) | 5.2.11 (5.2 LTS) | CVE-2025-64459 (CRITICAL), CVE-2024-53908, CVE-2025-57833 and other HIGH advisories in the 5.0 line |
| djangorestframework | 3.15.2 | 3.16.1 | see open item below |
| djangorestframework-simplejwt | 5.3.1 | 5.5.1 | known advisories in 5.3.x |
| pytest | 8.3.3 | 8.4.2 | known advisories in 8.3.x |
| frontend (all packages) | caret ranges | exact versions matching the current lockfile (react-router-dom / react-router 6.30.6, @remix-run/router 1.23.4, axios 1.21.0, vite 5.4.21) | unpinned ranges; patched react-router and axios |

## Open items / accepted risks

| ID | Package | Severity | Status | Justification | Owner | Review by |
|---|---|---|---|---|---|---|
| CVE-2026-114136, CVE-2026-114137, CVE-2026-114138 | djangorestframework 3.16.1 | HIGH | Check against the Trivy / Dependabot results | 3.16.1 is the newest release pinned here that is known to support Django 5.2. If a later release fixes these advisories, apply the Dependabot PR before deploying. If no fix exists yet, record here which DRF features are affected and why that exposure is acceptable. | Backend lead | 2026-12-04 |
| pytest advisories (if any are reported) | pytest 8.4.2 | — | Accepted if reported | pytest is used only for tests. It is never imported or run by the Gunicorn app process, so it cannot be reached through the deployed service. | Backend lead | 2027-02-04 |

## Review process

1. Before each deployment, run a dependency scan, for example
   `trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 .`
2. Each new HIGH/CRITICAL finding must be fixed, or added to the table above
   with a justification, an owner and a review date no more than 90 days away.
3. Remove an entry once a fixed version is pinned.
