# Embed Xplore — Khoj

A static, responsive prototype for the student-led Embed Xplore initiative.

## Pages
- `index.html`: public homepage and project roadmap
- `contribute.html`: role-specific contributor and volunteer interest form prototype
- `watch.html`: project watcher page, sample GenAI news feed and automation workflow preview
- `styles.css`: responsive styling
- `app.js`: language switching, phase cards and demo interactions

## Run locally
Open `index.html` in a modern browser. No build step or package installation is required.

## Important prototype limits
- Forms do not submit to a server or persist data.
- News cards are sample editorial content, not live news.
- Automated news publishing is a workflow preview, not a connected RSS/API pipeline.
- No authentication, database, email delivery, analytics or admin dashboard is configured.
- The language selector is a first-pass translation sample; some detailed labels and form options remain English.

## Next implementation steps
1. Fully translate every form label and validation state.
2. Add privacy notice, consent flow and age-appropriate safeguarding.
3. Connect a secure backend for application storage and admin review.
4. Connect approved RSS/API sources, scheduled collection, deduplication and summarization.
5. Choose whether each source/category requires manual review or can auto-publish after checks.
6. Add a public changelog and verified milestone evidence.

Do not collect real applicant data until a secure backend and privacy process are in place.