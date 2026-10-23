# Pathways Recruitment: End-to-End Test Guide

Covers the whole recruitment workflow (steps 1–34): green sheet, advertisement, shortlisting, interviews, reference checks, selection green sheet, offer, onboarding and joining. Sections 1–10 cover steps 1–12; sections 11–23 cover the rest. Work through the stages in order with one fresh test job. Tick a step when its result matches **Expect**. If a step fails, note the step number and send a screenshot or the error.

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

## 11. Before testing the later stages

User menu → Settings, Roles & Permissions, Master Setup.

- [ ] **11.1** Roles & Permissions: give real test users (your own inboxes) these roles: PNCO, CFO, Registrar, Vice Chancellor, Communications, IT Facilities. Also create 3 panellist users and 2 HR assessor users.
  **Expect:** each role shows at least one user.
- [ ] **11.2** Master Setup → Approval Chains: open the **Post-Interview Green Sheet** chain for your test job's track.
  **Expect:** a chain exists, e.g. Recruiter → PNCO → CFO → Registrar → VC. If none exists, create one before section 17.
- [ ] **11.3** Settings → check the sections Interview Rounds, Reference Checks, Offers & Appointment Orders (Duty Roles), Joining & Onboarding, Panel Honorarium.
  **Expect:** defaults filled in: 2 HR assessors, link valid 14 days, reviewer PNCO, signatory Registrar.
- [ ] **11.4** Master Setup: open Appointment Order Templates, Reference Check Templates and Scoring Rubrics.
  **Expect:** 5 appointment order templates; Admin, Faculty and Research reference templates; an HR Interaction rubric per track.
- [ ] **11.5** Email Setup → Emails by Stage: switch on the Interviews, Selection & Offer and Onboarding & Closure emails.
  **Expect:** no red "No recipients" chips on them.

## 12. Advertisement extras

Workflow steps 3, 6, 7 · Job page.

- [ ] **12.1** Approve a new job's Pre-Recruitment Green Sheet (last step).
  **Expect:** Registrar and Communications get "Green Sheet approved: prepare the official notification".
- [ ] **12.2** As Communications: job page → Publishing → Edit. Enter website, LinkedIn and Indeed links with dates, then Save.
  **Expect:** links shown on the card; an invalid URL is refused.
- [ ] **12.3** With the job Advertised, click **Share on LinkedIn**.
  **Expect:** LinkedIn's share window opens with the public job link.
- [ ] **12.4** Open `/jobs-feed.xml` and `/jobs-feed.json` in a browser.
  **Expect:** the advertised job is listed; draft and closed jobs are not; no internal fields.
- [ ] **12.5** Job page → Folder & Sharing.
  **Expect:** a folder path `Home/Pathways/<Department>/<Job>`.
- [ ] **12.6** Tag a colleague (a staff user with no Pathways role), add a note, then click **Tag and notify**.
  **Expect:** they get "Colleague tagged on a job" and, after logging in, can open this job's applications read-only, but no other job's.
- [ ] **12.7** Remove the colleague (×).
  **Expect:** they lose access.
- [ ] **12.8** Shortlisting card → **Edit committee**: add one member, set the deadline, upload an office order PDF.
  **Expect:** only the new member is emailed; the deadline and office order show on the card.
- [ ] **12.9** Set an Advertised job's deadline a few minutes in the past and wait for the hourly run (or run `bench --site pathways.local execute pathways.tasks.hourly`).
  **Expect:** the job and its notification are Closed; Communications and Recruiters get "Advertisement closed: take the ad down" exactly once.

## 13. HR interaction round

Workflow step 13 · Job page → Interviews; HR assessor's login.

- [ ] **13.1** Tick 2 shortlisted candidates → **Schedule Round 1 (HR)**. Add 2 HR assessors and try to add a third.
  **Expect:** a third is refused; after scheduling, candidates get the Round 1 invite and assessors get "HR assessor assigned (Round 1)".
- [ ] **13.2** Candidate portal: open the application and confirm the interview.
  **Expect:** RSVP shows Confirmed on the staff Interviews page.
- [ ] **13.3** As an HR assessor: Interview Panel.
  **Expect:** only their Round 1 rows are listed; Open shows the CV and SOP.
- [ ] **13.4** Score → submit without an outcome, then with **Recommend for final**, salary expectation, notice period and note.
  **Expect:** the outcome is required; the score bar says "of the HR sheet", not "needed for an offer"; the submission is saved.
- [ ] **13.5** As the recruiter: open the candidate's application page.
  **Expect:** the **HR interaction** card shows each assessor's outcome, score and note.
- [ ] **13.6** As an HR assessor: change the URL to an application not assigned to you.
  **Expect:** no access.

## 14. Final shortlist and selection committee

Workflow steps 14–16 · Job page → Interviews and Selection Committee.

- [ ] **14.1** Tick candidates → **Final shortlist ▾ → Add ticked to final shortlist**.
  **Expect:** a "Final" badge; they appear under Interviews → To schedule with next round Final.
- [ ] **14.2** **Final shortlist ▾ → Shortlisting Note…** → write a note, attach a file, **Save note**, then **Print (PDF)**.
  **Expect:** the PDF shows the note and the final shortlist.
- [ ] **14.3** Selection Committee → Edit: add 3 panellists, set a date and time, then Save.
  **Expect:** panellists are emailed. Desk → Event shows one event with the panellists plus VC and Registrar users.
- [ ] **14.4** Change the committee time and save again.
  **Expect:** the same event moves; no second event is created.
- [ ] **14.5** Tick the final shortlist → **Schedule Final**.
  **Expect:** candidates get the Interview Call Letter with date, time, link and RSVP.
- [ ] **14.6** **Panel files ▾ → Share files with the panel…**: tick the Notification, blank assessment sheets, Shortlisting Note and HR notes for one panellist.
  **Expect:** that panellist gets "Interview files shared"; Interview Panel → Shared documents lists the files and each opens.
- [ ] **14.7** **Panel files ▾**: download the Final interview schedule as Excel and PDF, and the blank assessment sheets.
  **Expect:** each file downloads and lists the scheduled candidates.

## 15. Panel scoring and decisions

Workflow steps 17–19 · Panellist's login; Interview Panel → Consolidated score sheet.

- [ ] **15.1** As a panellist: Interview Panel → candidate → Score. Enter scores and a verdict, **draw a signature**, then Submit.
  **Expect:** saved. With "Require signature" on in Settings, submitting without a signature is refused.
- [ ] **15.2** Repeat for the other panellists.
  **Expect:** the consolidated sheet shows each panellist's score and the average.
- [ ] **15.3** Desk → Interview Assessment → open one → Print → **Interview Assessment**.
  **Expect:** a form with scores, verdict, comments and the drawn signature.
- [ ] **15.4** Consolidated sheet: mark one candidate Selected, one Waitlisted, the rest Not selected. Click Export.
  **Expect:** statuses update; the Excel file matches the screen.

## 16. Regrets, thanks and honorarium

Workflow steps 32–33 · Consolidated sheet → "After the interviews" card; Panel Honorarium page.

- [ ] **16.1** Click **Send regrets** without ticking "Also send to waitlisted".
  **Expect:** the count excludes the waitlisted candidate; Not selected candidates get the Regret After Interview email.
- [ ] **16.2** Click Send regrets again.
  **Expect:** 0 to send; nobody gets a second email.
- [ ] **16.3** Click **Send thank-you to panel**.
  **Expect:** each panellist gets the thank-you once. Panel Honorarium lists one row per panellist; internal ones are "Not applicable" if "external experts only" is on.
- [ ] **16.4** As Recruiter: edit a row: amount, a PAN in the wrong format, then a correct one.
  **Expect:** the wrong PAN is refused.
- [ ] **16.5** Try **Mark paid** on a Pending row.
  **Expect:** refused until it is approved.
- [ ] **16.6** As CFO: Approve the row. Then Mark paid with a date and reference, and click Download Excel.
  **Expect:** status Paid; the Excel file includes the row.

## 17. Reference checks

Workflow step 21 · Applications → the Selected candidate → References panel.

- [ ] **17.1** Click **Start checks**.
  **Expect:** one check per referee the candidate entered, using the template for the job's track.
- [ ] **17.2** On one check, click **Email form link** (use your own email as the referee's).
  **Expect:** the referee email arrives; the panel shows the link with Copy.
- [ ] **17.3** Open the link in a private window (not logged in).
  **Expect:** candidate name, post and questions shown; no login asked.
- [ ] **17.4** Submit with a required question empty, then complete it.
  **Expect:** the empty question is flagged; after submitting, the recruiter gets "Reference received" and the check is Completed.
- [ ] **17.5** Open the same link again.
  **Expect:** "already submitted"; a made-up link says invalid.
- [ ] **17.6** On the second check, click **Record answers**, fill in the answers and click **Mark complete**.
  **Expect:** Completed, recorded by you.
- [ ] **17.7** Responses → write the summary → Save summary → Print.
  **Expect:** a printable reference check.
- [ ] **17.8** Candidate portal: open the application.
  **Expect:** nothing about reference checks is visible.

## 18. Post-interview (selection) green sheet

Workflow steps 20, 24, 25 · Consolidated sheet or job page → Selection card.

- [ ] **18.1** Click **Selection Green Sheet**.
  **Expect:** a draft with the selected and waitlisted candidates, process figures (applications, shortlisted, interviewed) and one fee row each.
- [ ] **18.2** Check the sections for the job's employment type.
  **Expect:** Pay Fixation only for Permanent; Deliverables for Consultant or contract; Funding for Research or grant-funded.
- [ ] **18.3** **Print → Panel Recommendation (for VC)**.
  **Expect:** a page with each candidate's averaged scores and the recommendation.
- [ ] **18.4** Attach a PDF as "Panel Recommendation (signed by VC)", Save Draft, then **Submit for Approval**.
  **Expect:** the first approver gets "Green Sheet awaiting approval" with a link to this sheet.
- [ ] **18.5** As the second approver, try to approve before the first.
  **Expect:** refused: not your step yet.
- [ ] **18.6** Return it with a reason, then **Revise & Resubmit**.
  **Expect:** a new draft with the same content; submitting restarts the chain.
- [ ] **18.7** Approve every step as each approver (or from My Approvals → Open full sheet).
  **Expect:** each next approver is emailed; at the end the status is Approved.
- [ ] **18.8** **Print → Green Sheet**, then **Upload signed copy**.
  **Expect:** the print matches the paper sheet's layout; the signed copy is listed.

## 19. Offer and appointment order

Workflow steps 22–23, 26–29 · Offers; Registrar and candidate logins.

- [ ] **19.1** Before the green sheet is approved, try **Create offer** for the candidate.
  **Expect:** refused: an approved selection green sheet is needed.
- [ ] **19.2** After approval: Applications → candidate → Offer card → **Create offer** (template: Suggest).
  **Expect:** the offer opens in Draft with the matching template.
- [ ] **19.3** Fill in Appointment Details, Compensation, Verbal Offer and Terms → Save Draft → **Preview Letter**.
  **Expect:** the letter shows the candidate, designation, pay and dates you entered.
- [ ] **19.4** **Submit for Review**. As PNCO, use **Return for Changes** without remarks, then with remarks.
  **Expect:** remarks are required; the drafter gets "Appointment order returned for changes"; status Draft.
- [ ] **19.5** Resubmit; as PNCO, **Approve for Signature**.
  **Expect:** the Registrar gets "Appointment order ready for signature".
- [ ] **19.6** As Registrar: **Sign** → draw a signature, tick "Save this as the signature for future orders", and Sign.
  **Expect:** status Signed by Registrar; Download PDF shows the signature, name and date.
- [ ] **19.7** **Send to Candidate**.
  **Expect:** the candidate gets the covering email with the PDF attached; status Sent.
- [ ] **19.8** Candidate portal → the application → Appointment order card: View letter, Download PDF, Upload signed copy, pick a joining date, then **Accept offer**.
  **Expect:** status Accepted on the staff side, with the joining date.
- [ ] **19.9** Staff: offer page → Signed Copies → **Upload scan**.
  **Expect:** the scan is listed separately from the candidate's signed copy.
- [ ] **19.10** Second candidate (optional): create, sign and send, then **Decline** with a reason in the portal.
  **Expect:** status Declined, with the reason shown.
- [ ] **19.11** Set an offer's acceptance deadline to yesterday and run `bench --site pathways.local execute pathways.tasks.daily`.
  **Expect:** the offer is Expired; the application is Not Selected.

## 20. Onboarding documents

Workflow step 34 · Automatic on acceptance; candidate portal; Documents.

- [ ] **20.1** Right after 19.8, check the candidate's inbox.
  **Expect:** one onboarding email with the joining date and portal link.
- [ ] **20.2** Candidate portal → the application → **Joining documents**.
  **Expect:** the checklist from Document Type Master; each row has Upload.
- [ ] **20.3** Upload all documents; Replace one.
  **Expect:** each row is Submitted; the replaced file is the new one.
- [ ] **20.4** As document verifier: **Documents → Onboarding Verification** → Review. Verify all but one; **Ask again** on that one, first without a reason and then with one.
  **Expect:** a reason is required; the candidate gets "Joining document needs resubmission" with the reason and sees it in the portal.
- [ ] **20.5** Candidate re-uploads; verifier verifies it.
  **Expect:** overall status Complete.
- [ ] **20.6** As the candidate, try to open another candidate's document collection (change the ID in the URL).
  **Expect:** no access.

## 21. Joining and IT/Facilities

Workflow step 31, folder 12 · Joinings; IT Requests (IT Facilities login).

- [ ] **21.1** **Joinings**.
  **Expect:** a draft joining for the accepted candidate, with their chosen date.
- [ ] **21.2** Open it: set reporting time, location and manager, and upload the bio and photo → **Confirm joining**.
  **Expect:** status Confirmed; IT & Facilities get the intimation email with the joiner's details.
- [ ] **21.3** Change the joining date and save, first without a reason and then with one.
  **Expect:** a reason is required; IT gets an updated email.
- [ ] **21.4** As IT Facilities: **IT Requests** → Update. Try **Complete & notify recruiter** with nothing ticked.
  **Expect:** refused until the laptop is ticked and an official email is entered.
- [ ] **21.5** Tick everything, enter the official email, and Complete.
  **Expect:** status Completed; the recruiter gets "IT & Facilities ready".
- [ ] **21.6** Back on the joining: **Mark joined**.
  **Expect:** the application is Joined; an Employee record is created (Desk → Employee) because documents were verified in 20.5.
- [ ] **21.7** Desk → Report → **New Joiners**, then **ERP Upload** → export.
  **Expect:** the joiner appears in both; the ERP Upload export includes designation, department, joining date and pay.

## 22. Reports, email log and import

- [ ] **22.1** **Reports**: filter by the test job's track.
  **Expect:** the Hiring Outcomes section shows offers (made, accepted, declined), joinings, acceptance rate and time to hire. Export includes them.
- [ ] **22.2** **Dashboard**.
  **Expect:** the new offer and joining tiles show your test records.
- [ ] **22.3** Sidebar → **Communications**: filter by the test job and click a row.
  **Expect:** every email from sections 12–21 is listed; the drawer shows the email as sent.
- [ ] **22.4** Application page → **Emails** card.
  **Expect:** only that candidate's emails.
- [ ] **22.5** Applications → Import → **Historical import**: download the template, add 2 rows with statuses Selected and Joined for a Closed job, upload, check the preview, then Import.
  **Expect:** imported with those statuses; no emails sent and no portal logins created.

## 23. Email check for the later stages

Email Setup → Recent, and Desk → Error Log.

| Email | Goes to | When |
|---|---|---|
| Green Sheet approved: prepare the official notification | Registrar, Communications | Pre-recruitment green sheet approved |
| Advertisement closed: take the ad down | Communications, Recruiter | Job auto-closes |
| Colleague tagged on a job | Tagged colleague | Tag and notify |
| HR assessor assigned (Round 1) | HR assessors | Round 1 scheduled with assessors |
| Interview files shared | Panellists | Panel files shared |
| Regret after interview | Candidate | Send regrets (consolidated sheet) |
| Thank you to panellists | Panellists | Send thank-you to panel |
| Reference check request / reminder | Referee | Email form link / daily reminder |
| Reference received | Recruiter who sent it | Referee submits |
| Green Sheet awaiting approval | Current approver | Each post-interview green sheet step |
| Appointment order ready for review / for signature / returned for changes | PNCO / Registrar / drafter | Offer workflow |
| Appointment order | Candidate (PDF attached) | Send to Candidate |
| Onboarding documents | Candidate | Offer accepted |
| Joining document needs resubmission | Candidate | Ask again on a document |
| IT & Facilities intimation | IT Facilities | Joining confirmed or date changed |
| IT & Facilities ready | Recruiter | IT request completed |

- [ ] **23.1** Email Setup → Recent: every email above that you triggered.
  **Expect:** status Sent, none Failed.
- [ ] **23.2** Desk → Error Log: search "Pathways".
  **Expect:** no new errors from your test run.

---

## Automated tests

Developers can run the automated suite (58 tests across every stage) before a manual run:

```bash
cd /home/jenifar/pathways
bench --site pathways.local set-config allow_tests true   # once per site
bench --site pathways.local run-tests --app pathways
```

**Expect:** `Ran 58 tests … OK`.
