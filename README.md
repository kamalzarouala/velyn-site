# velyn-site
Public website of the Velyn app (privacy policy, terms, support) and its health content feed.

- `content/library.json` — official public-domain health articles (womenshealth.gov), refreshed **every day** by `.github/workflows/content.yml`, with safety checks (an article is replaced only if it was fetched and is not suspiciously shorter). Changes: `content/CHANGELOG.md`.
- The app downloads `content/meta.json` once a day and, if the version changed, `content/library.json` (checked with SHA-256). Nothing about the user is sent.
