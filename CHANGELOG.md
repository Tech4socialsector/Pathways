# Changelog

All notable changes to Pathways are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/). While the version is below 1.0.0, a minor release may contain breaking changes; each one is listed under **Breaking Changes**.

Detailed notes for each release are in [spec/releases/](spec/releases/).

## [Unreleased]

## [0.4.0] - 2026-11-25

### Added
- Pathways can be installed as an app on desktop and mobile (Progressive Web App).
- Welcome page for signed-out visitors to `/pathways`, with **Sign in** and **Install app**.
- Install prompt for signed-in staff, with browser-specific steps where the browser has no install button; **Install app** in the user menu.

### Changed
- Phone layout: the sidebar opens as a drawer, search is a toggle in the top bar, and the notification panel fits the screen.
- Collapsed sidebar shows centred icons with tooltips.
- Table toolbars no longer squeeze filters on small screens.

### Technical
- `/pathways.webmanifest` and `/pathways-sw.js` served from the site root by a new page renderer (`pathways.pwa.PWAPage`).
- Service worker caches only hashed build assets and app icons. HTML pages, API responses and files are never cached.
- Pull requests must have a Conventional Commits title (GitHub Actions check) and use the new PR template.

### Migration Notes
- No database patches. Rebuild assets and restart (see [v0.4.0](spec/releases/v0.4.0.md)).

### Contributors
- Nishanth Clinton A, jenifarazim

### References
- [#1](https://github.com/Tech4socialsector/Pathways/pull/1), [a0fc465](https://github.com/Tech4socialsector/Pathways/commit/a0fc465), [d35786a](https://github.com/Tech4socialsector/Pathways/commit/d35786a)

## [0.3.0] - 2026-11-05

### Added
- **Interview replies on the candidate portal:** Confirm attendance, Request reschedule (reason and one to three preferred times) or Withdraw. Recruiters are emailed each reply.
- **Reschedule requests:** staff accept a preferred time (updated invite is sent), reject with a reason that is emailed to the candidate, or reschedule.
- **Interviews page:** one tab per stage (To schedule, Scheduled, Reschedule, Completed, Cancelled) and a round switch (All rounds, Round 1 (HR), Final interview).
- **BCC** on schedule, reschedule/edit and cancel interview emails.
- **Staff Welcome email** (Email Setup › Staff & Access) for new staff users: their roles, the menu sections they open, their approval steps and a set-password link.
- **Applications list:** Interviews filter with counts and an optional Interview column.
- **Candidate portal:** sidebar navigation (My Applications, Openings, Change password), notification bell, and a slide-out menu on phones.
- **Candidate forgot-password** from the Change password page.
- **Shortlisting Committee setup:** a role for each member and a member count checked against the minimum and maximum in Settings.
- **Dashboard drill-down:** JD Status filter and column.
- **Position onboarding documents:** each Position can list the documents its new joiners submit. Verifiers can add or remove a document for one new joiner.
- **Honorarium to Finance:** the recruitment team enters an external expert's amount, PAN and bank details and emails them to the Finance team.

### Changed
- Application form saves to the candidate's account 1.2 seconds after each change. The footer shows Unsaved changes / Saving… / All changes saved. Leaving or refreshing saves the draft first.
- The application submitted screen no longer shows "What happens next".
- Dropdown options are sorted A–Z, with "Other" and "Prefer not to say" kept last.
- Master Setup no longer lists Institutions, Specialisations and UGC NET Subjects. Their data is kept and the application form still uses it.
- Reference check templates reject duplicate questions.
- Candidate portal no longer shows status badges, the stage tracker or the Profile page. `/portal/profile` opens Change password.
- Portal login emails describe what candidates can do on the portal. Saved templates are updated only where they still contain the old sentences.
- Interviews: one **Export CSV** per tab, from the selection bar.
- Table column headers are easier to read.
- Position **Employment Type** options are Permanent, Consultant and Contract.

### Fixed
- Users with Pathways roles other than Admin and Recruiter can now read Departments.

### Security
- Candidate APIs no longer return application or offer status, and the Application's internal pipeline fields are hidden from candidates.
- Pathways Admin can manage users, roles and Pathways permissions, with guards: it cannot take over non-Pathways roles, change or remove the Pathways Admin role, or remove that role from itself.
- The Staff Welcome email is never copied to anyone, because it carries a set-password link.
- Interview emails reject an address in both CC and BCC, allow at most 20 addresses per field, and never blind-copy the recipient.
- New Google Meet events hide the guest list, and existing events have it hidden when they are next updated.
- Candidate password-reset requests are limited to three per hour.
- Only the candidate who owns an interview can reply to it, only for open future interviews.

### Technical
- New child DocType **Position Onboarding Document**.
- Interview: new reply options (Confirmed, Reschedule Requested, Withdrawn; Declined kept) and fields for reply time, reason, preferred times and the reschedule decision.
- Panel Honorarium: new bank, PAN, attachment and Sent to Finance fields; approval and payment fields removed.
- Recruitment Email Rule: new stage **Staff & Access**; new rules `staff_welcome`, `interview_rsvp_update`, `reschedule_request_declined`, `honorarium_to_finance`.
- `on_session_creation` hook clears a candidate's temporary-password flag after a password reset.
- Pathways Admin gains submit/cancel on Post-Interview Green Sheet, export on Communication Log and Application Status History, and read/delete on Application Draft.
- The compiled frontend (`pathways/public/frontend`, `pathways/www/pathways.html`) is no longer committed. It is built at deploy time. A root `package.json` lets `bench build` run the frontend build.
- Candidate profile endpoints `get_my_profile` and `update_my_profile` removed.

### Breaking Changes
- **Panel Honorarium workflow:** statuses are now Pending, Sent to Finance and Not applicable. Approved and Paid records become Sent to Finance. The approval step is removed, so the Honorarium Approver Roles setting is no longer used.
- **Frontend build required on every deploy:** run `bench build --app pathways`.
- **Position Employment Type** no longer offers Grant-funded. A Position that has it must be changed before it can be saved.
- **Pathways Settings:** where the status override role was System Manager, it becomes Pathways Admin (System Manager can still override). Pathways Admin is added as an offer reviewer.

### Migration Notes
- Run `bench --site <site> migrate`. Patches: `seed_email_events` (#staff-welcome, #interview-reply, #reschedule-request-declined), `honorarium_to_finance`, `portal_login_wording` (two runs), `pathways_admin_full_access`.

### Contributors
- Nishanth Clinton A, jenifarazim

### References
- [bdf2fbe](https://github.com/Tech4socialsector/Pathways/commit/bdf2fbe), [708ca88](https://github.com/Tech4socialsector/Pathways/commit/708ca88), [75d4fff](https://github.com/Tech4socialsector/Pathways/commit/75d4fff), [b24e591](https://github.com/Tech4socialsector/Pathways/commit/b24e591), [6ae1904](https://github.com/Tech4socialsector/Pathways/commit/6ae1904), [db3899b](https://github.com/Tech4socialsector/Pathways/commit/db3899b), [452e977](https://github.com/Tech4socialsector/Pathways/commit/452e977), [ebc7070](https://github.com/Tech4socialsector/Pathways/commit/ebc7070), [9b3fbe6](https://github.com/Tech4socialsector/Pathways/commit/9b3fbe6), [a104539](https://github.com/Tech4socialsector/Pathways/commit/a104539), [62a2cfa](https://github.com/Tech4socialsector/Pathways/commit/62a2cfa), [c31caea](https://github.com/Tech4socialsector/Pathways/commit/c31caea), [0510415](https://github.com/Tech4socialsector/Pathways/commit/0510415), [19646a6](https://github.com/Tech4socialsector/Pathways/commit/19646a6), [8800273](https://github.com/Tech4socialsector/Pathways/commit/8800273), [e8706db](https://github.com/Tech4socialsector/Pathways/commit/e8706db), [876ff7f](https://github.com/Tech4socialsector/Pathways/commit/876ff7f), [61f50b9](https://github.com/Tech4socialsector/Pathways/commit/61f50b9)

## [0.2.0] - 2026-10-28

### Added
- **Onboarding module:** one Onboarding page with tabs for Onboarding Verification, Joinings and IT Requests, replacing the separate menu items.
- **Portal access for existing logins:** when someone with an existing site login applies as a guest, they get candidate portal access and a one-time email to sign in with their current password. Staff and disabled logins are not changed.
- **CC and BCC** when sending an appointment order to a candidate.
- **Create new** option at the end of Master Setup link dropdowns for System Managers. It opens the new record in a new tab.
- Edit or view icon on each row of the Master Setup lists.

### Changed
- Documents page lists only application documents. Onboarding checklists moved to the Onboarding page.
- Old `/joinings`, `/it-requests` and `/documents?tab=onboarding` links redirect to the matching Onboarding tab.
- Faculty shortlisting criteria have guidance text. Only empty guidance is filled on existing sites.
- Position: Hiring Manager Role is hidden. Saved values are kept.
- Scoring Rubric Template: Pass Threshold % appears only once the rubric has criteria.

### Fixed
- Deleting a record from Master Setup failed.
- Applying for a job with a Single Choice screening question failed.
- Email and letter previews opened behind the Send and Sign dialogs.
- Pressing Enter in a Master Setup form saved the record without confirmation.

### Technical
- Demo data script: `bench --site <site> execute pathways.demo_data.create` (and `.delete`). It uses fictional `@example.org` people.
- Job Opening **Files Folder** field length raised to 255 characters.

### Breaking Changes
- **DocType renames:** `Designation` → `Pathways Designation` and `Employee` → `Pathways Employee`, so Pathways can run alongside ERPNext. Screens still say "Designation" and "Employee". Custom reports, scripts or integrations that use the old names must be updated.
- **Scoring mode "Pass/Fail Only" removed.** Existing rubrics move to Weighted Score. A Shortlisting rubric with no criteria still means a shortlist/reject decision with remarks.

### Migration Notes
- Run `bench --site <site> migrate`. Pre-sync patches `rename_designation_doctype` and `rename_employee_doctype` rename in place when no other app defines those DocTypes. Otherwise post-sync patches `copy_shared_designations` and `copy_shared_employees` copy the Pathways records and leave the other app's DocType intact. Also runs `faculty_shortlisting_guidance`, `seed_email_events` (#candidate-portal-existing-account) and `drop_pass_fail_scoring_mode`.

### Contributors
- Nishanth Clinton A, jenifarazim

### References
- [81a75d4](https://github.com/Tech4socialsector/Pathways/commit/81a75d4), [198ff48](https://github.com/Tech4socialsector/Pathways/commit/198ff48), [4608092](https://github.com/Tech4socialsector/Pathways/commit/4608092), [e2c2ce4](https://github.com/Tech4socialsector/Pathways/commit/e2c2ce4), [02280b2](https://github.com/Tech4socialsector/Pathways/commit/02280b2), [085e904](https://github.com/Tech4socialsector/Pathways/commit/085e904), [f0f4ae3](https://github.com/Tech4socialsector/Pathways/commit/f0f4ae3)

## [0.1.0] - 2026-10-23

Initial release baseline. There is no earlier version.

### Added
- Staff app at `/pathways` and candidate portal at `/pathways/portal`, built with Vue and frappe-ui.
- **Job and advertisement:** pre-recruitment green sheet with configurable approval chain, job openings with per-track application forms, notifications and corrigenda, publishing tracker, Indeed XML and JSON job feeds, auto-close, job folders and colleague tagging.
- **Applications:** candidate portal (apply, view applications, reply to interviews, offers, documents), candidate accounts, Excel/CSV import.
- **Shortlisting:** committee with office order, eligibility check, scoring rubrics, document ZIP and data export, regret emails.
- **Interviews:** HR interaction round, final shortlist and shortlisting note, selection committee, Google Meet links, file sharing with the panel, panel scoring and consolidated score sheet.
- **Selection:** reference checks, post-interview green sheet with approval chain, regrets after interview, panel thank-you and honorarium.
- **Offer and joining:** appointment order templates, review and signature, PDF letter, candidate accept/decline on the portal or recorded by staff, onboarding documents, joining confirmation, IT/Facilities requests.
- **Reporting:** dashboard, analytics, email log, and the Recruitment Pipeline, New Joiners and ERP Upload reports.
- Configurable roles, approval chains, email rules and templates.
- Hourly and daily scheduled jobs for closing advertisements, reminders, offer expiry and draft cleanup.

### Contributors
- jenifarazim

### References
- [888f148](https://github.com/Tech4socialsector/Pathways/commit/888f148)

[Unreleased]: https://github.com/Tech4socialsector/Pathways/compare/v0.4.0...TFSS
[0.4.0]: https://github.com/Tech4socialsector/Pathways/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/Tech4socialsector/Pathways/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/Tech4socialsector/Pathways/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Tech4socialsector/Pathways/tree/v0.1.0
