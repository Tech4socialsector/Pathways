# Pathways Recruitment: End-to-End Test Guide

Covers the recruitment workflow from the green sheet through shortlisting, regret emails and the candidate portal (workflow steps 1–12). Work through the stages in order with one fresh test job. Tick a step when its result matches **Expect**. If a step fails, note the step number and send a screenshot or the error.

| | |
|---|---|
| Staff app | http://127.0.0.1:8017/pathways |
| Candidate portal | http://127.0.0.1:8017/pathways/portal/jobs |
| Desk (records, Error Log) | http://127.0.0.1:8017/app |
| Tip | Use two browsers: staff in one, the candidate in a private window |

---

## 0. Before you start

User menu (top right) → Email Setup, Roles & Permissions. Master Setup is in the sidebar.

> **Emails go to real addresses.** Use your own inboxes for the candidate and for the staff users you assign to roles. Administrator never receives Pathways emails.

- [ ] **0.1** Email Setup → send a test email to yourself.
  **Expect:** it arrives within a minute or two.
- [ ] **0.2** Email Setup → set the **Reply-to address** and save.
  **Expect:** a toast "Replies will go to …".
- [ ] **0.3** Email Setup → Emails by Stage: check every rule you want is switched on.
  **Expect:** no orange "No one holds …" or red "No recipients" chips on the rules you plan to test.
- [ ] **0.4** Roles & Permissions: give real users the roles you'll test (at least Registrar, Communications, Recruiter and the approver roles in your chain). Create 2–3 staff users for the shortlisting committee.
  **Expect:** the role's user count goes up; the user picker lets you choose a user and click Add.
- [ ] **0.5** Master Setup: open the Position you'll use and check the job code, department, designation, employment type and form switches (PhD, NET, publications…).
  **Expect:** values are filled in; employment type is not blank.

## 1. Job opening and green sheet

Workflow steps 1–2 · Job Openings → New, then the job page.

- [ ] **1.1** Job Openings → New: pick the Position.
  **Expect:** department, designation, track and employment type fill in.
- [ ] **1.2** Try to advertise before the green sheet is approved.
  **Expect:** blocked with a message.
- [ ] **1.3** Green Sheet card: fill in the justification and ad duration, upload a JD and a supporting document, then submit.
  **Expect:** status Under Approval; the first approver gets the "Green Sheet awaiting approval" email and a bell badge.
- [ ] **1.4** As the approver: click the bell.
  **Expect:** a dropdown listing the sheet; clicking it opens My Approvals with the review dialog open.
- [ ] **1.5** Review dialog: check the job details, justification, documents and approval chain, then Return with a reason.
  **Expect:** the sheet goes to Returned for Revision; the job page shows it can be revised.
- [ ] **1.6** Revise and resubmit, then approve every step.
  **Expect:** each next approver is emailed; after the last step the sheet is Approved and the job shows Approved.
- [ ] **1.7** Upload the signed copy on the green sheet.
  **Expect:** the JD, supporting document and signed copy are all listed.

## 2. Advertisement and corrigendum

Workflow steps 2–4 · Job page: Application Form panel, Notification & Corrigenda.

- [ ] **2.1** Application Form panel: set **Applications open** to tomorrow and a deadline after it. Check the instructions and screening questions (including an "Other" follow-up).
  **Expect:** a start date after the deadline is refused.
- [ ] **2.2** Notification & Corrigenda: enter the notification number, date and link or file.
  **Expect:** saved and shown on the card.
- [ ] **2.3** Advertise the job.
  **Expect:** status Advertised; Registrar and Communications users get "Advertisement live".
- [ ] **2.4** Candidate portal → Openings: find the job.
  **Expect:** the card says "Opens …"; the apply page says applications aren't open yet.
- [ ] **2.5** Change the start date to now.
  **Expect:** the job shows "Apply by …" and the form opens.
- [ ] **2.6** Issue a corrigendum extending the deadline.
  **Expect:** the job deadline moves; Registrar and Communications get "Corrigendum issued"; a Closed job reopens to Advertised.

## 3. Candidate applies

Workflow steps 5–6 · Private window, not logged in, at `/pathways/portal/jobs`.

- [ ] **3.1** Open the job → View & apply → View instructions.
  **Expect:** general and job instructions in a dialog.
- [ ] **3.2** Submit with required fields empty.
  **Expect:** an error under each missing field.
- [ ] **3.3** Answer a question with "Other" or the trigger answer.
  **Expect:** the follow-up field appears only then.
- [ ] **3.4** Faculty job only: check the sections the Position switches on (specialization, PhD, NET, experience months, publications with min/max).
  **Expect:** only switched-on sections appear; CGPA needs both the value and the scale.
- [ ] **3.5** Upload files and submit with a new email address.
  **Expect:** success page with the application ID and a note that portal login details were emailed.
- [ ] **3.6** Check that inbox.
  **Expect:** two emails: "Application received", and "Your NLSIU Careers login" with the username (Candidate ID) and a temporary password.
- [ ] **3.7** Apply again to the same job with the same email.
  **Expect:** refused: one application per email per position.
- [ ] **3.8** Try to apply with a staff email.
  **Expect:** refused: staff emails can't apply.

## 4. Candidate portal

Login link from the email · same private window.

- [ ] **4.1** Log in with the Candidate ID (e.g. `PWY-CAND-2026-00001`) and the temporary password.
  **Expect:** sent straight to "Set your own password"; other pages redirect back there.
- [ ] **4.2** Try a wrong temporary password, a password shorter than 8 characters, and the same password again.
  **Expect:** each is refused with a clear message.
- [ ] **4.3** Set a valid new password, log out (confirm), then log in with the email and the new password.
  **Expect:** a "Log out?" confirmation; login works with the email too.
- [ ] **4.4** Open My Applications.
  **Expect:** welcome banner, summary tiles and one card per application with the stage stepper.
- [ ] **4.5** Open an application.
  **Expect:** progress line, My documents (each opens in the viewer) and My application, view only.
- [ ] **4.6** Compare with the job's form switches.
  **Expect:** only sections the job asked for appear (no NET/PhD/Publications tabs on an Admin job); no eligibility or internal fields.
- [ ] **4.7** Change the URL to another candidate's application ID.
  **Expect:** "We couldn't open this application".

## 5. Shortlisting committee and documents

Workflow steps 7–9 · Job page → Shortlisting card.

- [ ] **5.1** Set up the committee with 2–3 members.
  **Expect:** members listed on the card; each gets the committee invitation email.
- [ ] **5.2** Download the All applicants, Eligible only and Shortlisted ZIPs.
  **Expect:** one folder per document type (CV, SOP, Transcripts…).
- [ ] **5.3** Log in as a committee member.
  **Expect:** they see this job's applications only, not other jobs'.

## 6. Eligibility check

Workflow step 10 · Application page, or the Applications list bulk actions.

- [ ] **6.1** Mark one candidate Eligible.
  **Expect:** status Under Review; the Shortlisting card's Eligible count goes up.
- [ ] **6.2** Mark one Not Eligible without a reason, then with one.
  **Expect:** a reason is required; status Not Selected; a note in the activity log.
- [ ] **6.3** Applications list: select several → bulk eligibility.
  **Expect:** a result dialog with successes and any failures.
- [ ] **6.4** Candidate portal: open the Not Eligible application.
  **Expect:** it still shows Under Review until a regret is sent.

## 7. Shortlisting and the 1:N target

Workflow steps 11–12 · Application page → Shortlisting card; job page → Shortlisting card.

- [ ] **7.1** Try to score a Pending or Not Eligible candidate.
  **Expect:** blocked until they're marked Eligible.
- [ ] **7.2** Faculty or Research job: enter scores, then Shortlist.
  **Expect:** a score above a criterion's maximum is refused; a confirmation dialog; status Shortlisted; progress and activity update.
- [ ] **7.3** Admin job: Shortlist or Reject.
  **Expect:** no score boxes; remarks are required.
- [ ] **7.4** Edit a decision (Edit → change → confirm).
  **Expect:** the status follows the new decision.
- [ ] **7.5** Job page → Change ratio.
  **Expect:** target = vacancies × ratio; the bar turns orange when over the target.

## 8. Regret emails

Before Round 1 · Job page → Shortlisting card → Regret emails.

- [ ] **8.1** Check the counts: Not eligible / Not shortlisted / Already sent.
  **Expect:** they match the candidates you rejected.
- [ ] **8.2** Send regret emails → tick one group → send.
  **Expect:** "N regret emails queued"; those candidates get the Regret Mail; "Regret email sent" in each activity log.
- [ ] **8.3** Send again.
  **Expect:** already-sent candidates are skipped (0 for that group).
- [ ] **8.4** Candidate portal: open a rejected application.
  **Expect:** it now shows "Not taken forward".
- [ ] **8.5** Reply to the regret email.
  **Expect:** the reply goes to your reply-to address.

## 9. Closing, dashboard and bulk actions

The scheduler runs these hourly and daily while `bench start` is running.

- [ ] **9.1** Set a job's deadline a few minutes in the past and wait for the hourly run.
  **Expect:** the job becomes Closed; the apply page refuses new applications.
- [ ] **9.2** Set a deadline for tomorrow.
  **Expect:** the Recruiter gets "Advertisement closing within 24 hours" after the daily run.
- [ ] **9.3** Dashboard: change filters, then click Search.
  **Expect:** nothing reloads until Search; cards drill down to the matching records.
- [ ] **9.4** Dashboard: click a job row, a deadline and a recent application.
  **Expect:** each opens the right page.
- [ ] **9.5** Job Openings and Applications lists: select rows → change status, export CSV, delete a test record.
  **Expect:** a result dialog; the CSV has the visible columns.

## 10. Email log check

Email Setup → Recent, and Desk → Error Log.

| Email | Goes to | When | Default |
|---|---|---|---|
| Green Sheet awaiting approval | Current approvers | Each approval step | On |
| Advertisement live | Registrar, Communications | Job advertised | On |
| Corrigendum issued | Registrar, Communications | Corrigendum saved | On |
| Advertisement closing within 24 hours | Recruiter | Daily, the day before the deadline | On |
| Application received | Candidate | Application submitted | On |
| Candidate portal login | Candidate | First application from an email | On |
| Shortlisting committee invitation | Committee members | Committee set up | On |
| Regret after screening | Candidate | Sent from the Shortlisting card | On |
| Regret: not eligible / not shortlisted | Candidate | Instantly on each decision | Off |
| Shortlisted | Candidate | Committee shortlists | Off |

- [ ] **10.1** Email Setup → Recent: every email you triggered above is listed.
  **Expect:** status Sent, none Failed.
- [ ] **10.2** Desk → Error Log: search "Pathways email".
  **Expect:** no "email failed" entries. A "no recipients" entry means a role has nobody in it.

---

**Not covered yet:** the interview stage onwards (Round 1, call letters, panel scoring, post-interview green sheet, offers, onboarding). Those emails exist in Email Setup, but their screens are the next build.
