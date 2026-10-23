### Pathways

NLSIU Recruitment Management: a Frappe app covering the whole recruitment workflow, from the pre-advertisement green sheet to the new joiner's first day.

It has a staff app at `/pathways` and a candidate portal at `/pathways/portal`, both built in Vue with frappe-ui. Approval chains, roles, email rules and templates can all be configured without code changes.

### What it covers

| Stage | Features |
|---|---|
| Job and advertisement | Pre-recruitment green sheet with configurable approval chain, job opening and per-track application form, notification and corrigenda, publishing tracker, Indeed XML and JSON job feeds, auto-close, job folders and colleague tagging |
| Applications | Candidate portal (apply, track status, RSVP, offers, documents), candidate accounts, Excel/CSV import including historical cycles |
| Shortlisting | Committee with office order, eligibility check, scoring rubrics, 1:N target, document ZIP and data export, regret emails |
| Interviews | HR interaction round with HR assessors and scoring, final shortlist and shortlisting note, selection committee with calendar block, Google Meet links, file sharing with the panel, panel scoring with signatures, consolidated score sheet |
| Selection | Reference checks (referee web form or recorded by recruiter), post-interview green sheet with approval chain, regrets after interview, panel thank-you and honorarium |
| Offer and joining | Appointment order templates, PNC review, Registrar signature, PDF letter, candidate accept/decline, onboarding document collection and verification, joining confirmation, IT/Facilities requests |
| Reporting | Dashboard, recruitment and hiring analytics (offers, joinings, time to hire), email log, New Joiners and ERP Upload reports |

### Requirements

- Frappe v16 (bench-managed), Python 3.14+
- Node 18+ and Yarn 1.x (to build the frontend)
- MariaDB and Redis, as for any bench
- An outgoing Email Account in Frappe; Pathways sends many emails
- Optional: Google Workspace credentials for Google Meet links and calendar sync

### Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/Tech4socialsector/Pathways.git --branch TFSS
bench --site <your-site> install-app pathways
bench --site <your-site> migrate
```

`install-app` creates the roles, settings, email rules and templates, scoring rubrics, approval chains, appointment-order and reference-check templates, and other master data. The patches in `pathways/patches.txt` keep existing sites in step on `migrate`.

#### Building the frontend

The compiled frontend is committed under `pathways/public/frontend`. Rebuild it after changing anything in `frontend/src`:

```bash
cd apps/pathways/frontend
yarn install
yarn build        # writes pathways/public/frontend and pathways/www/pathways.html
```

For live development, run `yarn dev` in `frontend/` alongside `bench start`. It proxies API calls to the bench.

#### Running

```bash
bench start
```

The scheduler must be running for the automatic steps:

| Schedule | Jobs |
|---|---|
| Hourly | Close expired advertisements and their notifications, and email Communications |
| Daily | Closing-soon reminders, interview reminders, offer expiry, referee reminders, cleanup of stale application drafts |

Make sure the scheduler is enabled on the site: `bench --site <your-site> enable-scheduler`.

### First-time setup

Log in as a System Manager and open `/pathways`:

1. **Email Setup** (user menu): send a test email, set the reply-to address and switch on the emails you want.
2. **Roles & Permissions**: give users the Pathways roles (Recruiter, PNCO, CFO, Registrar, Vice Chancellor, Communications, IT Facilities, and so on).
3. **Master Setup**: check the approval chains for each track, positions, scoring rubrics, appointment order templates, reference check templates and onboarding documents.
4. **Settings**: interview rounds, reference checks, offers (reviewer and signatory roles), joining defaults, honorarium amounts, Google Meet.

Part A of the [User Guide](docs/USER_GUIDE.md) has the full checklist.

### Documentation

- [User Guide](docs/USER_GUIDE.md): step-by-step guide to running a recruitment, by role and workflow step
- [Testing Guide](docs/TESTING_GUIDE.md): manual end-to-end test checklist for all stages

### Tests

```bash
bench --site <your-site> set-config allow_tests true   # once per site
bench --site <your-site> run-tests --app pathways
bench --site <your-site> run-tests --module pathways.tests.test_offer   # one module
```

Tests are in `pathways/tests/`, one module per stage: platform, HR round, reference checks, post-interview green sheet, offer, onboarding, and selection communications. They roll back their own records. Run them on a development site, not production.

### Project layout

```
pathways/
  api/            whitelisted endpoints used by the frontend, one module per area
  utils/          shared logic: approvals, email events, onboarding, permissions helpers
  pathways/
    doctype/      DocTypes
    print_format/ green sheets, panel recommendation, assessment, reference check, shortlisting note
    report/       Recruitment Pipeline, New Joiners, ERP Upload
  patches/        data patches (see patches.txt)
  tests/          automated tests
  tasks.py        scheduled jobs
  permissions.py  row-level permission rules
frontend/src/
  pages/          staff pages and candidate-portal/
  components/     UI components grouped by area
  services/       API wrappers
docs/             user and testing guides
```

Emails are only sent through `pathways.utils.communication.send_event`. Each event is defined in `pathways/utils/email_events.py`, and staff edit the rules and templates on the Email Setup page.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/pathways
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
