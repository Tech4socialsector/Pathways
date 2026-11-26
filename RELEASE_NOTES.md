# Pathways Release Notes

Pathways is NLSIU's recruitment management app on the Frappe Framework. It has a staff app at `/pathways` and a candidate portal at `/pathways/portal`.

| Version | Date | Highlights |
|---|---|---|
| [0.4.0](#pathways-040) | 2026-11-25 | Installable app, phone layout |
| [0.3.0](#pathways-030) | 2026-11-05 | Interview replies and reschedule requests, new candidate portal, honorarium to Finance, Pathways Admin access |
| [0.2.0](#pathways-020) | 2026-10-28 | Works alongside ERPNext, Onboarding page, Master Setup fixes |
| [0.1.0](#pathways-010) | 2026-10-23 | First release: the full recruitment workflow |

Technical detail for each version is in [spec/releases/](spec/releases/), and the full history is in the [Changelog](CHANGELOG.md).

---

## Pathways 0.4.0

**Release date:** 2026-11-25 · **Type:** Minor · [Technical notes](spec/releases/v0.4.0.md)

### Overview
Staff can install Pathways as an app on their computer or phone, and the staff app is easier to use on small screens. There are no database changes and no breaking changes.

### New features
- **Installable app.** Signed-in staff are offered an install prompt. Browsers without a built-in install button get step-by-step instructions. **Install app** is also in the user menu.
- **Welcome page.** Visitors to `/pathways` who are not signed in see **Sign in** and **Install app**.

### Improvements
- On phones the sidebar opens as a drawer, search is a button in the top bar, and the notification panel fits the screen.
- When the sidebar is collapsed, its icons are centred and show their names on hover.
- Table filters no longer get squeezed on small screens.
- Pull request titles are checked for the standard format, and a pull request template has been added.

### Security
- The installed app keeps only the app's own files (code, styles, icons) on the device. Pages, recruitment data and documents are never stored, so nothing remains on a shared device after logout.

### Who is affected
- **Administrators:** no setup needed. The site must be served over HTTPS for the app to be installable.
- **Recruitment staff and committee members:** can install Pathways and use it on a phone.
- **Candidates:** the candidate portal is unchanged.

### Known limitations
- Pathways needs an internet connection. Without one, the installed app shows an offline page.
- Some browsers, such as Safari on iOS, have no install button. The app shows manual steps instead.

### Deployment
```bash
bench --site <site> backup
cd apps/pathways && git fetch && git checkout v0.4.0 && cd ../..
bench --site <site> migrate
bench build --app pathways
bench restart
```
There are no database patches in this release.

---

## Pathways 0.3.0

**Release date:** 2026-11-05 · **Type:** Minor, with breaking changes · [Technical notes](spec/releases/v0.3.0.md)

### Overview
Candidates can reply to interview invitations on the portal, and staff handle reschedule requests in one place. The Interviews page is organised by stage, the candidate portal is simpler, honorarium details for external experts go straight to Finance, and Pathways Admin can manage access without a System Manager.

### New features
- **Interview replies.** Candidates can confirm attendance, ask to reschedule (with a reason and one to three preferred times) or withdraw from an interview. Recruiters get an email for each reply.
- **Reschedule requests.** Staff accept a preferred time, which sends an updated invitation. They can also reject the request with a reason, which is emailed to the candidate.
- **Interviews page by stage.** It has tabs for To schedule, Scheduled, Reschedule, Completed and Cancelled, and a switch for All rounds, Round 1 (HR) or Final interview.
- **BCC on interview emails** when scheduling, rescheduling or cancelling.
- **Staff Welcome email.** New staff users receive an email that explains their roles, what they can open, their approval steps and how to set their password.
- **Interview filter on Applications.** Shows where each candidate is in the interview process.
- **New candidate portal layout.** A menu with My Applications, Openings and Change password, a notification bell, and a slide-out menu on phones.
- **Candidate forgot-password** from the Change password page.
- **Shortlisting Committee roles.** Each member has a role (such as Chairperson or Subject expert), and the number of members is checked against the limits in Settings.
- **JD Status on the dashboard drill-down.**
- **Onboarding documents for each Position.** New joiners are asked for that Position's documents. Verifiers can add or remove a document for one new joiner.
- **Honorarium to Finance.** The recruitment team enters an external expert's amount, PAN and bank details, and Pathways emails them to the Finance team.

### Improvements
- The application form saves automatically and shows whether all changes are saved. Leaving or refreshing the page saves the draft first.
- Dropdown lists are sorted A–Z, with "Other" and "Prefer not to say" last.
- Reference check templates no longer allow the same question twice.
- Interviews have one **Export CSV** per tab.
- Table headings are easier to read.
- Master Setup no longer lists Institutions, Specialisations and UGC NET Subjects. Their data is kept and the application form still uses it.

### Bug fixes
- Users with Pathways roles other than Admin and Recruiter can now see Departments.

### Security
- Candidates no longer see their application or offer status, or the recruitment team's internal fields. Progress reaches them by email.
- Pathways Admin can manage users and roles, but cannot take over non-Pathways roles or change its own role.
- The Staff Welcome email is never copied to anyone, because it contains a set-password link.
- Interview emails reject an address in both CC and BCC.
- Google Meet guest lists are hidden from invitees.
- Candidate password-reset requests are limited to three per hour.

### Who is affected
- **Administrators:** review the new emails in Email Setup, and add the Finance team's address to "Honorarium details to Finance". Check the offer reviewer roles and the status override role in Pathways Settings.
- **Recruitment staff:** new Interviews layout, reschedule requests to answer, and honorarium details to send to Finance.
- **Committee members:** Shortlisting Committee members now have a role.
- **Candidates:** new portal layout, interview replies, forgot-password, and automatic saving of applications. Application status is no longer shown on the portal.

### Breaking changes
- **Honorarium:** the approve-and-pay steps are replaced by **Sent to Finance**. Existing Approved and Paid records are moved to Sent to Finance automatically.
- **Deployment:** the built frontend is no longer included in the code. Every deployment must run `bench build --app pathways`.
- **Position Employment Type** no longer offers Grant-funded. A Position that uses it must be changed before it can be saved.
- **Pathways Settings:** Pathways Admin becomes the status override role (where it was System Manager) and an offer reviewer.

### Deployment
```bash
bench --site <site> backup --with-files
cd apps/pathways && git fetch && git checkout v0.3.0 && cd ../..
bench setup requirements --node
bench --site <site> migrate
bench build --app pathways
bench restart
```

---

## Pathways 0.2.0

**Release date:** 2026-10-28 · **Type:** Minor, with breaking changes · [Technical notes](spec/releases/v0.2.0.md)

### Overview
Pathways can now be installed on the same site as ERPNext. Onboarding has its own page, people who already have a login can use the candidate portal, and Master Setup forms are safer to use.

### New features
- **Onboarding page.** Onboarding Verification, Joinings and IT Requests are together on one page. Old links still work.
- **Portal access for existing logins.** People who already have a login on the site and apply as guests get candidate portal access and a one-time email to sign in with their current password.
- **CC and BCC** when sending an appointment order to a candidate.
- **Create new from a dropdown.** System Managers can create a missing master record from a Master Setup dropdown. It opens in a new tab.

### Improvements
- The Documents page lists only application documents.
- Faculty shortlisting criteria include guidance for the committee.
- Master Setup lists show an edit or view icon on each row.

### Bug fixes
- Deleting a record from Master Setup failed.
- Applying for a job with a Single Choice screening question failed.
- Email and letter previews opened behind the dialog they came from.
- Pressing Enter in a Master Setup form saved the record without confirmation.

### Who is affected
- **Administrators:** run `migrate`. Update any custom reports or scripts that use the old Designation or Employee names.
- **Recruitment staff:** Onboarding is one menu item, and appointment orders can be copied to others.
- **Candidates:** people with an existing login can see their applications.

### Breaking changes
- **Designation** and **Employee** are renamed to **Pathways Designation** and **Pathways Employee**. Screens still show "Designation" and "Employee", and existing records are kept.
- The **Pass/Fail Only** scoring mode is removed. Existing rubrics move to Weighted Score automatically.

### Deployment
```bash
bench --site <site> backup --with-files
cd apps/pathways && git fetch && git checkout v0.2.0 && cd ../..
bench --site <site> migrate
bench restart
```

---

## Pathways 0.1.0

**Release date:** 2026-10-23 · **Type:** Initial release · [Technical notes](spec/releases/v0.1.0.md)

### Overview
The first release of Pathways. It covers recruitment from the pre-advertisement green sheet to the new joiner's first day. Approval chains, roles, email rules and templates can be configured without code changes.

### Features
- **Job and advertisement:** green sheet with approval chain, job openings, notifications and corrigenda, publishing tracker, job feeds for Indeed and the website, automatic closing.
- **Applications:** candidate portal and accounts, Excel/CSV import.
- **Shortlisting:** committee, eligibility check, scoring rubrics, document and data export, regret emails.
- **Interviews:** HR round, selection committee, Google Meet links, file sharing with the panel, panel scoring, consolidated scores.
- **Selection:** reference checks, post-interview green sheet, regrets, panel thank-you and honorarium.
- **Offer and joining:** appointment orders with review and signature, candidate accept/decline, onboarding documents, joining confirmation, IT/Facilities requests.
- **Reporting:** dashboard, analytics, email log, and the Recruitment Pipeline, New Joiners and ERP Upload reports.

### Deployment
```bash
bench get-app https://github.com/Tech4socialsector/Pathways.git --branch TFSS
cd apps/pathways && git checkout v0.1.0 && cd ../..
bench --site <site> install-app pathways
bench --site <site> migrate
bench --site <site> enable-scheduler
bench restart
```

---

## Acknowledgements

Thanks to Nishanth Clinton A and jenifarazim for their work on Pathways.
