# Pathways Recruitment: Step-by-Step User Guide

How to run one recruitment in Pathways, from the pre-advertisement green sheet to the new joiner's first day. Steps follow NLSIU's 34-step recruitment workflow; the step numbers are shown in brackets. Each step says **who** does it and **where**.

| | |
|---|---|
| Staff app | `/pathways` |
| Candidate portal | `/pathways/portal/jobs` |
| Referee form (no login) | `/pathways/referee/<link from email>` |
| Job feeds | `/jobs-feed.xml` (Indeed) · `/jobs-feed.json` (NLSIU website) |
| Desk (records, print formats, Error Log) | `/app` |

Steps marked *(manual)* happen outside Pathways, but their signed copies are uploaded back.

---

## Part A: One-time setup (Pathways Admin)

Do this once before the first live recruitment.

1. **Email.** User menu → **Email Setup**:
   - Send a test email to yourself and set the reply-to address.
   - Under **Emails by Stage**, check that every email you want is switched on. Red or orange chips mean nobody holds the recipient role yet.
2. **People and roles.** User menu → **Roles & Permissions**. Give real users these roles:
   - Recruiter, PNCO, CFO, Registrar, Vice Chancellor, Communications, IT Facilities;
   - the deans and directors who sit in approval chains.
   Committee members get their committee role automatically when they are added to a committee.
3. **Approval chains.** **Master Setup → Approval Chains**:
   - Check the chain for each track for **Pre-Recruitment Green Sheet** and for **Post-Interview Green Sheet**.
   - Pathways added *Recruiter → PNCO → CFO → Registrar → VC* only where a track had no post-interview chain. On this site that is Faculty.
   - The existing Admin and Research chains use *Director People Culture* rather than PNCO. Edit them if that is wrong.
   - You can add separate Permanent/Consultant chains using the *Employment type* field.
4. **Settings.** User menu → **Settings** (more fields are in Desk → *Pathways Settings*):

   | Section | What to set |
   |---|---|
   | Interview Rounds | HR assessors per interview (default 2); whether a drawn signature is required on assessment forms; roles whose calendars are blocked for the selection committee (VC, Registrar); length of the committee sitting |
   | Reference Checks | how many days a referee's link stays valid (14); remind the referee after N days (3; 0 = never) |
   | Offers & Appointment Orders | offer reviewer roles (PNCO) and signatory roles (Registrar), under *Duty Roles*; whether an offer needs an approved post-interview green sheet (on); signatory title; saved Registrar signature image (Desk) |
   | Joining & Onboarding | default reporting location and time; *Document Verifier Roles* |
   | Panel Honorarium | default amounts for internal and external panellists; "external experts only"; honorarium approver roles (CFO, Admin) |

5. **Master Setup templates:**
   - **Appointment Order Templates**: 5 are seeded (Permanent non-teaching, Consultant, Faculty, Research/Project, Contract). Edit the wording or add more.
   - **Reference Check Templates**: Admin, Faculty and Research question sets, taken from the existing forms.
   - **Scoring Rubrics**: shortlisting, HR interaction and final interview rubrics per track.
   - **Document Type Master**: which onboarding documents each joiner must upload (*Used In = Onboarding/Both*).
6. **Google Meet** (optional): Settings → Google Meet tab, if interview links and calendar blocks should be created automatically.

---

## Part B: Running a recruitment

### 1. Job opening, green sheet and advertisement (steps 1–7)

1. **Recruiter:** in **Job Openings → New**, pick the Position. Department, track and employment type fill in.
2. **Recruiter** (step 1): in the job's **Green Sheet** card, enter the justification and ad duration, upload the JD, then **Submit**. Each approver in the chain gets an email and a bell notification in turn.
3. **Approvers:** open **My Approvals** (or the link in the email), then **Approve**, or **Return** with a reason. If the sheet is returned, the recruiter clicks **Revise & Resubmit**.
4. **Automatic** (step 3): when the sheet is approved, the Registrar's Office and Communications are emailed to prepare the official notification.
5. **Registrar's Office / Communications:** on the job page, **Notification & Corrigenda → Edit**: notification number, link and PDF.
6. **Recruiter** (steps 2, 4): in the **Application Form** card, check the form, then set the job to **Advertised**. The public application link goes live.
7. **Communications** (step 3): on the job page, **Publishing → Edit**. Enter the website, LinkedIn and Indeed links with dates, then **Save**.
   - **Share on LinkedIn** opens LinkedIn's share box.
   - Give `/jobs-feed.xml` to Indeed and `/jobs-feed.json` to the web team once. From then on, every advertised job appears there automatically.
8. **Recruiter** (step 5): the day before the deadline, you get a reminder email and a ToDo. To extend, click **Extend deadline**. This issues a corrigendum (attach its PDF) and emails the Registrar and Communications.
9. **Automatic** (step 6): at the deadline, the job and its notification close. Communications and Recruiters are emailed to take the ad down.
10. **Recruiter** (step 7): on the job page, **Folder & Sharing** shows the job's folder, *Home/Pathways/&lt;Department&gt;/&lt;Job&gt;*.
    - Under **Tag a colleague**, pick a person, add a note and click **Tag and notify**. They get read-only access to this job's applications.
    - Click **×** to remove access.

### 2. Shortlisting (steps 8–12)

1. **Recruiter** (step 8): on the job page, Shortlisting card → **Set up committee**. Add the members, the office order reference and deadline, upload the office order, and save. Members are emailed.
   - Use **Edit committee** later; only newly added members are emailed.
2. **Recruiter / committee** (steps 9–10): **Applications**, filtered by job.
   - **Export** gives the data dump.
   - **Download Documents** gives a ZIP split into CV / SOP / Writing Sample folders.
3. **Committee:** mark each candidate **Eligible** or **Not eligible** (with a reason), then score the eligible ones on the shortlisting sheet (step 11).
4. **PNCO / Recruiter** (step 12): the Shortlisting card shows progress against the 1:5 target. Finalise the shortlist.
5. **Recruiter:** **Send regrets** in the Shortlisting card emails everyone not eligible or not shortlisted, once each.

### 3. HR interaction round (step 13; optional)

1. **Recruiter:** on the job page, **Interviews** → tick candidates → **Schedule Round 1 (HR)**.
   - Set the date, time and mode or link, and add the HR assessors (up to 2 by default).
   - The candidates get an invite with RSVP buttons. The assessors are emailed and added to the Meet event.
2. **Candidate:** confirms or declines from the email or the portal.
3. **HR assessor:** **Interview Panel** → the *Round 1 (HR)* row → **Score**.
   - Read the CV and SOP, score the criteria, and choose **Recommend for final / Hold / Not recommended**.
   - Add the salary expectation, notice period and HR note, sign, and click **Submit scores**.
4. Reschedule, edit or cancel any interview from **⋯** on its row. The candidate is emailed.

The HR outcome appears on the candidate's application page, in the **HR interaction** card.

### 4. Final shortlist and selection committee (steps 14–16)

1. **Recruiter / PNCO** (step 14):
   - Tick candidates → **Final shortlist ▾ → Add ticked to final shortlist**.
   - Then **Final shortlist ▾ → Shortlisting Note…**: write the note, add attachments, **Save note**, and **Print (PDF)** if needed.
2. **Recruiter** (step 15): **Selection Committee → Edit**. Add 3–5 panellists and set the date and time, then save.
   - Panellists are emailed.
   - One calendar event blocks the panel's, the VC's and the Registrar's calendars. It moves if you reschedule, and is cancelled if you clear the date.
3. **Recruiter** (step 16): tick the final shortlist → **Schedule Final interview**. Candidates receive the interview call letter with RSVP.
4. **Recruiter** (step 16): **Panel files ▾ → Share files with the panel…**. Tick what each panellist gets:
   - candidate CV / SOP / writing sample;
   - the Notification, panel details and blank assessment sheets;
   - the Shortlisting Note and HR interaction notes;
   - the interview schedule.

   The same menu downloads the interview schedule (Excel or PDF) and blank assessment sheets.
5. **Panellists:** **Interview Panel → Shared documents** to read the files before the interview.

### 5. Interviews and scoring (steps 17–19)

1. **Panellist** (steps 17–18): **Interview Panel** → candidate → **Score**.
   - Score each criterion, choose a verdict, and add comments and area of specialisation.
   - **Sign** on screen, then **Submit scores**.
2. **Recruiter** (if a panellist scored on paper): enter the scores on their behalf from the same screen.
3. **Recruiter** (step 19): **Interview Panel → Consolidated score sheet** for the job.
   - Scores are averaged automatically.
   - Mark each candidate **Selected / Waitlisted / Not selected**.
   - **Export** gives an Excel copy. Desk → Interview Assessment → **Print → Interview Assessment** prints a panellist's signed form.

### 6. After the interviews: regrets, thanks, honorarium (steps 32–33)

On the consolidated score sheet, in the **After the interviews** card:

1. **Send regrets** (step 32) emails interviewed candidates who were not selected, once each.
   - Tick *Also send to waitlisted* only when the waitlist is released.
2. **Send thank-you to panel** (step 33) emails each panellist once and creates an honorarium record for each.
3. **Recruiter / PNCO:** **Panel Honorarium** page → pencil icon. Set the amount and PAN, attach the bank/consent form, or mark a row *Not applicable*.
4. **CFO / Admin:** **Approve** individual rows, or tick several and approve them together.
5. **Finance:** **Mark paid** with the date and payment reference. **Download Excel** exports the list.

### 7. Reference checks (step 21)

1. **Recruiter:** Applications → open the candidate. In the **References** panel, click **Start checks**. One check is created per referee the candidate gave.
   - **Add referee** adds another person; the pencil icon edits one.
2. Choose one of two ways for each referee:
   - **Online form:** click **Email form link**. The referee opens the link without logging in, answers and clicks **Submit reference**, and you get an email. Unanswered referees are reminded automatically. **Resend link** issues a fresh link.
   - **By phone:** click **Record answers**, type the replies, then **Mark complete**.
3. Open **Responses**, write the **Overall assessment summary**, then **Save summary**. Click **Print** for the file.

Candidates never see reference responses.

### 8. Post-interview green sheet (steps 20, 24–25)

1. **Recruiter:** on the consolidated score sheet, click **Selection Green Sheet** (or, on the job page, **Selection → Raise Selection Green Sheet**). A draft opens, filled in from the selection outcomes and process figures.
   - Use **Re-draft from outcomes** if the outcomes change.
2. **Recruiter / PNCO:** complete the sections:
   - appointment details;
   - pay fixation (Permanent jobs);
   - deliverables (Consultant or contract jobs);
   - funding (Research or grant-funded jobs).
3. **Step 20** *(manual signature)*: **Print → Panel Recommendation (for VC)**, get it signed by the VC, then upload the scan under **Annexures → Panel Recommendation (signed by VC)**. Attach the score sheet, reference checks and salary proof, then **Save Draft**.
4. **Recruiter:** **Submit for Approval**. The sheet goes to Recruiter → PNCO → CFO → Registrar → VC in turn.
5. **Approvers:** open it from the email or **My Approvals → Open full sheet**, then **Approve**, or **Return** with a reason.
   - A returned sheet is fixed with **Revise & Resubmit**.
   - **More → Withdraw** stops a sheet in progress.
6. **Step 25:** **Print → Green Sheet**, collect the physical signatures, then **Upload signed copy**.

### 9. Offer and appointment order (steps 22–23, 26–29)

1. **PNCO** (steps 22–23, *verbal*): agree the salary and joining date with the selected candidate by phone.
2. **Recruiter / PNCO:** Applications → candidate → **Offer** card → **Create offer** (or **Offers → Create Offer**). This needs the approved post-interview green sheet.
   - Leave the template on *Suggest*, or pick one.
3. Fill in **Appointment Details**, **Compensation** (with remarks), **Verbal Offer** (date, who discussed it, what was agreed) and **Terms**.
4. **Save Draft**, then **Preview Letter**, then **Submit for Review**.
5. **Asst. Manager PNC / PNCO** (step 26): **Offers → Under Review** → open the offer → **Approve for Signature**, or **Return for Changes** with remarks.
6. **Registrar** (step 27): open the offer → **Sign**. Draw a signature, or use the saved one; tick *Save this as the signature for future orders* the first time. The signed PDF is generated.
7. **Recruiter / Registrar's Office** (step 28): **Send to Candidate**, adjusting the acceptance deadline if needed. The candidate receives the covering email with the PDF.
8. **Candidate:** **Portal → My Applications → the application → Appointment order** card:
   - **View letter** / **Download PDF**;
   - choose a joining date and click **Accept offer**, or **Decline** with a reason;
   - **Upload signed copy**.
9. **Recruiter** (step 29): on the offer page, **Signed Copies → Upload scan** files the Registrar-signed scan.

Offers not answered by the deadline expire automatically each night.

### 10. Onboarding documents (step 34)

Accepting the offer automatically:
- creates the candidate's document checklist;
- creates a draft joining record;
- sends the onboarding email with the portal link.

1. **Candidate:** Portal → the application → **Joining documents** → **Upload** each document (**Replace** to change one). Status and any reason to re-upload are shown there.
2. **Document verifier:** **Documents → Onboarding Verification** → **Review**. Preview each file, then **Verify**, or **Ask again** with a reason. The candidate is emailed the reason.

### 11. Joining and IT/Facilities (step 31, folder 12)

1. **Recruiter / PNCO:** **Joinings** → open the joiner.
   - Set the date of joining, reporting time, location and manager, and upload the bio write-up and directory photo.
   - Click **Confirm joining**. IT & Facilities are emailed.
   - Changing the date later asks for a reason and emails IT again.
   - Offers accepted before this feature existed appear at the top with **Start onboarding**.
2. **IT & Facilities:** **IT Requests** → **Update**.
   - Tick laptop, official email created, access card and seating, and enter the official email ID.
   - **Save progress** keeps partial work. **Complete & notify recruiter** finishes the request.
3. **Recruiter / PNCO:** on the day, click **Mark joined** (or **No-show**). The application becomes *Joined*. The Employee record is created once every mandatory document is verified.
4. *(Manual, step 30)*: close the physical file.

---

## Part C: Monitoring and reports

| Need | Where |
|---|---|
| Everything waiting for me | **Dashboard**, **My Approvals** |
| Pipeline, offers, joinings, time-to-hire, acceptance rate | **Reports**. Filter by track, job or dates; **Export** to Excel |
| Every email sent, and what it said | Sidebar → **Communications** (or the **Emails** card on an application) |
| New joiners register | Desk → Report → **New Joiners** |
| Upload of joiners into the ERP | Desk → Report → **ERP Upload** → export CSV/Excel |
| Load past recruitments | **Applications → Import → Historical import**. Download the template, upload, check the preview, then import. No emails are sent and no logins are created |

---

## Part D: Who sees what

| Role | Main screens |
|---|---|
| Pathways Recruiter | Everything in a recruitment except approvals and signing |
| Pathways PNCO | Green sheets, final shortlist, offer review, joinings |
| CFO / Registrar / VC | **My Approvals**. Registrar also signs appointment orders. VC and Registrar calendars are blocked for selection committees |
| Shortlisting committee member | Only the applications of jobs they are on |
| Selection committee member / HR assessor | **Interview Panel**: only their candidates and shared files |
| Tagged colleague | Read-only view of the jobs they are tagged on |
| Communications | Notification, publishing tracker, ad-closed emails |
| IT Facilities | **IT Requests** |
| Candidate | Portal: their own applications, interviews, offer and documents. Never reference checks or scores |
| Referee | Only their own form, through the emailed link |
