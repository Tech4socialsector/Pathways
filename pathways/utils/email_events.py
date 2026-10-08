# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Every recruitment email, by workflow stage: the default Recruitment Email
Rule and Email Template for each. ensure_email_events() creates whatever is
missing and never overwrites what staff have edited on the Email Setup page.

automatic=False marks emails whose stage is not built yet: they can be
prepared now and are sent once that stage exists."""

import frappe

SIGN_OFF = "<p>Kind regards,<br>Recruitment Team<br>NLSIU, Bengaluru</p>"

TEMPLATES = {
	# Workflow folder: none (step 6). Plain acknowledgement.
	"Application Acknowledgement": (
		"Application Received: {{ job_title }}",
		"<p>Dear {{ candidate_name }},</p>"
		"<p>Greetings from National Law School of India University (NLSIU), Bangalore!</p>"
		"<p>Thank you for applying for the position of <b>{{ job_title }}</b>. Your application "
		"(ID: <b>{{ application_id }}</b>) has been received. Please keep this ID for any communication with us.</p>"
		"<p>If you have any queries, you can email us at {{ contact_email or 'recruitment@nls.ac.in' }}.</p>" + SIGN_OFF,
	),
	# Workflow folder: 4. Shortlisting / Email to Shortlisting Committee.
	"Shortlisting Committee Invitation": (
		"Shortlisting committee: {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>Thank you for agreeing to be a part of the shortlisting committee for the <b>{{ job_title }}</b>. "
		"We have received {{ application_count }} responses for the advertisement.</p>"
		"<p>Please note the essential steps to be followed in the process of shortlisting candidates for interview:</p><ul>"
		"<li>1:{{ ratio }} candidates, if available, need to be shortlisted for interviews.</li>"
		"<li>Please first check whether the candidate is eligible for the position that they have applied for. The eligibility "
		"criteria is mentioned in the ad, which is available <a href=\"{{ posting_link }}\">here</a>. Please note the reason for "
		"ineligibility in the remarks. This is to enable a round of cross-checking to ensure that eligible candidates have not "
		"been erroneously excluded, and vice versa. Ineligible candidates need not be assigned a score.</li>"
		"<li>Please score the candidates in the form provided. Please note that you should arrive at a common score as a panel. "
		"We do not require each panelist to score the candidate individually.</li>"
		"<li>Once you have completed the shortlisting process, please submit the scores on the platform.</li>"
		"<li>Please keep the shortlist confidential until the candidates have been invited for interview by the PnC team.</li></ul>"
		"<p><b>Important</b> - While shortlisting for interviews, please ensure that the candidates shortlisted come from diverse "
		"backgrounds. At NLSIU we value diversity and believe it enriches the environment, fosters inclusion, and strengthens our "
		"community by bringing varied perspectives and experiences.</p>"
		"<p>Please find the link to access the applications along with the relevant documents uploaded: "
		"<a href=\"{{ job_link }}\">{{ job_link }}</a></p>"
		"{% if deadline %}<p>We request you to complete the shortlisting by <b>{{ deadline }}</b>.</p>{% endif %}"
		"<p>Thank you for your time and effort. Please let me know if you have any queries.</p>" + SIGN_OFF,
	),
	# Workflow folder: 5. Round 1 Interview / Regret Mail and 9. Regret Mails / Regret Email Template.
	"Regret Mail": (
		"Important: Update on your job application for {{ job_title }}",
		"<p>Dear Candidate,</p>"
		"<p>We have an update on your application for the position of {{ job_title }} at NLSIU Bangalore.</p>"
		"<p>We regret to inform you that we will not be moving forward with your application. We truly appreciate the time "
		"and effort put in by you for your application.</p>"
		"<p>Please note that this decision is not a reflection of your abilities, and we encourage you to apply for positions "
		"that may/will come up in the future.</p>"
		"<p>Please keep a lookout on the website - "
		"<a href=\"https://www.nls.ac.in/news-and-events/work-with-us/\">https://www.nls.ac.in/news-and-events/work-with-us/</a></p>"
		+ SIGN_OFF,
	),
	# Workflow folder: 5. Round 1 Interview / Email to Candidate.
	"Interview Invite (Round 1)": (
		"Action Required : Interviews - {{ job_title }}",
		"<p>Dear Applicant,</p>"
		"<p>Greetings from National Law School of India University (NLSIU), Bangalore!</p>"
		"<p>This is with reference to your interviews (Round 1) for the position {{ job_title }} at NLS. We are pleased to "
		"inform you that your application has been selected for the Round 1 interview. This round is scheduled on "
		"<b>{{ interview_date_time }}</b> (IST){% if interview_location %} in person at <b>{{ interview_location }}</b>{% else %} via video conferencing{% endif %}.</p>"
		"{% if interview_location %}<ol>"
		"<li>Please arrive ten minutes before your start time at {{ interview_location }}.</li>"
		"{% else %}<p>Please find below the {{ meeting_platform or 'Teams' }} link for the meeting:<br>"
		"<a href=\"{{ meeting_link }}\">{{ meeting_link }}</a></p><ol>"
		"<li>Please login into the {{ meeting_platform or 'Teams' }} meeting ten minutes before your start time and please "
		"remain logged in. You will be admitted into the call once the panel is ready.</li>{% endif %}"
		"<li>While our earnest attempt is to bring each candidate into the interview room as per schedule, we request you to "
		"bear with us if there is a delay.<br><b>IMPORTANT</b> - We request you to keep a two-hour window for the interview to "
		"factor for any delay.</li>"
		"<li>If you face any technical glitches, please be assured that our team will reach out to you. You can also email us "
		"at {{ contact_email or 'recruitment@nls.ac.in' }}.</li></ol>"
		"<p>Please confirm your participation by replying to this email{% if rsvp_deadline %} by <b>{{ rsvp_deadline }}</b>{% endif %}."
		"{% if rsvp_link %} You can also confirm or decline in your candidate portal: <a href=\"{{ rsvp_link }}\">{{ rsvp_link }}</a>{% endif %}</p>" + SIGN_OFF,
	),
	# No template in the workflow folder: invitation to the selection panel.
	"Selection Committee Invitation": (
		"Selection committee: {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>Thank you for agreeing to be on the selection committee for <b>{{ job_title }}</b> ({{ department }}).</p>"
		"{% if interview_date %}<p>The interviews are planned for <b>{{ interview_date }}</b>{% if interview_time %} from <b>{{ interview_time }}</b>{% endif %}."
		"{% if candidate_count %} {{ candidate_count }} candidate(s) have been shortlisted.{% endif %}</p>{% endif %}"
		"<p>Panel: {{ panel }}</p>"
		"<p>The candidates' CVs, statements of purpose, writing samples and the interview assessment form will be available "
		"to you on Pathways: <a href=\"{{ job_link }}\">{{ job_link }}</a></p>"
		"<p>The interview schedule and meeting link will follow.</p>" + SIGN_OFF,
	),
	# Workflow folder: 6. Final Interview / Interview Call Letter.
	"Interview Call Letter": (
		"Action Required : Interviews for the position of {{ job_title }}",
		"<p>Dear Applicant,</p>"
		"<p>Greetings from National Law School of India University (NLSIU), Bangalore!</p>"
		"<p>This is with reference to your application for the position of {{ job_title }} in our institution.</p>"
		"<p>We are pleased to inform you that your application has been shortlisted, and your interview is scheduled "
		"{% if interview_location %}in person{% else %}via video conferencing{% endif %} on:</p>"
		"<p>Date - <b>{{ interview_date }}</b><br>Day - <b>{{ interview_day }}</b><br>Time - <b>{{ interview_time }}</b><br>"
		"Mode - {{ interview_mode or 'Online' }}{% if interview_location %}<br>Venue - <b>{{ interview_location }}</b>{% endif %}</p>"
		"{% if track == 'Faculty' %}<p>The interview will be in 2 parts:</p><ol>"
		"<li>A talk by you on your pedagogical approach to teaching, with at least one example (approximately 3 to 5 minutes). "
		"Please note that due to a paucity of time, slide presentations are not possible.</li>"
		"<li>A discussion with the Selection Committee (approximately 10 minutes).</li></ol>{% endif %}"
		"{% if interview_location %}<p>Please note:</p><ol>"
		"<li>Please report at {{ interview_location }} twenty minutes{% if login_time %} ({{ login_time }}){% endif %} before your "
		"start time. You will be called in once the Committee is ready.</li>"
		"{% else %}<p>Please find the details of the meeting ID and password for the {{ meeting_platform or 'Teams' }} call:<br>"
		"<a href=\"{{ meeting_link }}\">{{ meeting_link }}</a>{% if meeting_details %}<br>{{ meeting_details }}{% endif %}</p>"
		"<p>Please note:</p><ol>"
		"<li>Please login into the {{ meeting_platform or 'Teams' }} meeting twenty minutes{% if login_time %} ({{ login_time }}){% endif %} "
		"before your start time and please remain logged in. You will be admitted into the call once the Committee is ready. "
		"Please ensure that your camera and microphone are switched on when you enter the meeting room.</li>{% endif %}"
		"<li>While our earnest attempt is to bring each candidate into the interview room as per schedule, we request you to "
		"bear with us if there is a delay.</li>"
		"<li>If you face any technical glitches, please be assured that our recruitment team will reach out to you. You can "
		"also email us at {{ contact_email or 'recruitment@nls.ac.in' }}.</li></ol>"
		"{% if rsvp_link %}<p>Please confirm or decline your attendance in your candidate portal: "
		"<a href=\"{{ rsvp_link }}\">{{ rsvp_link }}</a></p>{% endif %}"
		+ SIGN_OFF +
		"<p><b>General Instructions:</b></p><ol>"
		"<li>Ensure your room is well-illuminated and free of any background/external noise.</li>"
		"<li>Ensure your computer's mic and camera are functioning well, with the background being clear.</li>"
		"<li>Test your internet speed/stability, keep a backup.</li></ol>",
	),
	# Workflow folder: 10. Appointment Order email / Letter to Candidate.
	"Appointment Order Covering Note": (
		"Appointment Letter - {{ job_title }}",
		"<p>Dear {{ candidate_name }},</p>"
		"<p>Greetings from the National Law School of India University, Bangalore!</p>"
		"<p>Please find attached the Appointment Letter as {{ job_title }} at NLSIU. Request you to confirm your acceptance "
		"and send a signed scanned copy of the appointment letter with a reply all to this email by "
		"<b>{{ acceptance_deadline }}</b>.</p>"
		"<p>Please also indicate your earliest date of joining in the same email.</p>"
		"<p>You may get in touch with {{ pnc_contacts or 'the People and Culture team' }}"
		"{% if pnc_contacts %}, from the People and Culture team,{% endif %} if you need any further clarifications or support.</p>"
		"<p>Regards,<br>Registrar's Office</p>",
	),
	"Candidate Portal Login": (
		"Your NLSIU Careers login: track your application",
		"<p>Dear {{ candidate_name }},</p>"
		"<p>Thank you for applying. You can now log in to the NLSIU Careers portal to track the status of your application(s) "
		"and view what you submitted.</p>"
		"<table style=\"border-collapse:collapse;margin:12px 0\">"
		"<tr><td style=\"padding:4px 16px 4px 0;color:#555\">Login page</td><td><a href=\"{{ login_link }}\">{{ login_link }}</a></td></tr>"
		"<tr><td style=\"padding:4px 16px 4px 0;color:#555\">Username</td><td><b>{{ username }}</b> (your Candidate ID)</td></tr>"
		"<tr><td style=\"padding:4px 16px 4px 0;color:#555\">Temporary password</td><td><b>{{ temporary_password }}</b></td></tr>"
		"</table>"
		"<p>You will be asked to set your own password the first time you log in. You can also log in with your email address "
		"instead of the username. Please do not share these details with anyone.</p>" + SIGN_OFF,
	),
	"Green Sheet Approval Request": (
		"Approval needed: Green Sheet for {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>The Pre-Recruitment Green Sheet <b>{{ doc_name }}</b> for <b>{{ job_title }}</b> is awaiting your approval "
		"({{ approver_label }}).</p><p><a href=\"{{ link }}\">Open it in Pathways</a> to approve or return it.</p>" + SIGN_OFF,
	),
	"Job Advertised Notice": (
		"Advertisement live: {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>The advertisement for <b>{{ job_title }}</b> ({{ job_code }}, {{ department }}, {{ vacancies }} vacancies) is now live.</p>"
		"<p>{% if notification_number %}Notification: {{ notification_number }}<br>{% endif %}"
		"Applications close: <b>{{ deadline }}</b><br>Job posting: <a href=\"{{ posting_link }}\">{{ posting_link }}</a></p>"
		"<p>Registrar's Office: please issue the official notification. Communications: please publish it on the NLSIU "
		"website and social media (LinkedIn, Indeed).</p>" + SIGN_OFF,
	),
	"Corrigendum Notice": (
		"Corrigendum issued: {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>A corrigendum has been issued for <b>{{ job_title }}</b>: {{ change }}.</p>"
		"{% if remarks %}<p>{{ remarks }}</p>{% endif %}"
		"<p>Please update the website and social media posts. Job posting: <a href=\"{{ posting_link }}\">{{ posting_link }}</a></p>" + SIGN_OFF,
	),
	"Advertisement Closing Soon": (
		"Closing within 24 hours: {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>The advertisement for <b>{{ job_title }}</b> closes on <b>{{ deadline }}</b> and has received "
		"{{ application_count }} application(s).</p>"
		"<p>If more applications are needed, extend the deadline from the job page (this issues a corrigendum): "
		"<a href=\"{{ job_link }}\">{{ job_link }}</a></p>" + SIGN_OFF,
	),
	"Shortlisted Notice": (
		"Update on your application: {{ job_title }}",
		"<p>Dear {{ candidate_name }},</p>"
		"<p>We are pleased to inform you that your application ({{ application_id }}) for <b>{{ job_title }}</b> has been "
		"shortlisted. Details of the next round will be shared with you by email shortly.</p>" + SIGN_OFF,
	),
	"Interview Reminder": (
		"Reminder: your interview for {{ job_title }}",
		"<p>Dear {{ candidate_name }},</p>"
		"<p>This is a reminder of your interview for <b>{{ job_title }}</b> on <b>{{ interview_date_time }}</b>.</p>"
		"{% if meeting_link %}<p>Meeting link: <a href=\"{{ meeting_link }}\">{{ meeting_link }}</a></p>{% endif %}"
		"<p>Please log in ten minutes before your start time.</p>" + SIGN_OFF,
	),
	"Panel Thank You": (
		"Thank you: interviews for {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>Thank you for being on the selection committee for <b>{{ job_title }}</b>. We are grateful for your time and "
		"guidance. The PnC team will be in touch about the honorarium.</p>" + SIGN_OFF,
	),
	# Workflow folder: 11. Onboarding Email.
	"Onboarding Documents": (
		"DOCUMENTS TO BE SUBMITTED",
		"<p>Dear {{ candidate_name }},</p>"
		"<p>We are looking forward to welcoming you to NLSIU!</p>"
		"<p>On the day of joining, kindly bring the softcopy and Photocopy of the below mentioned documents</p>"
		"<table style=\"border-collapse:collapse\" border=\"1\" cellpadding=\"6\">"
		"<tr><td>1</td><td>PAN (MANDATORY)</td></tr>"
		"<tr><td>2</td><td>AADHAAR (MANDATORY)</td></tr>"
		"<tr><td>3</td><td>DIGITAL PHOTOGRAPH (MANDATORY)</td></tr>"
		"<tr><td>4</td><td>PASSPORT (OPTIONAL)</td></tr>"
		"<tr><td>5</td><td>COPY OF THE SIGNED APPOINTMENT ORDER (MANDATORY)</td></tr>"
		"<tr><td>6</td><td>XTH STD CERTIFICATE (MANDATORY)</td></tr>"
		"<tr><td>7</td><td>XIITH STD CERTIFICATE (MANDATORY)</td></tr>"
		"<tr><td>8</td><td>GRADUATION - I CERTIFICATE (MANDATORY)</td></tr>"
		"<tr><td>9</td><td>GRADUATION - TRANSCRIPTS (MANDATORY)</td></tr>"
		"<tr><td>10</td><td>GRADUATION - II CERTIFICATE (IF APPLICABLE)</td></tr>"
		"<tr><td>11</td><td>POST GRADUATION - I CERTIFICATE (IF APPLICABLE)</td></tr>"
		"<tr><td>12</td><td>POST GRADUATION - TRANSCRIPTS (IF APPLICABLE)</td></tr>"
		"<tr><td>13</td><td>POST GRADUATION - II CERTIFICATE (IF APPLICABLE)</td></tr>"
		"<tr><td>14</td><td>LATEST PAYSLIPS (MANDATORY)</td></tr>"
		"<tr><td>15</td><td>RELIEVING LETTER (MANDATORY)</td></tr>"
		"<tr><td>16</td><td>NO OBJECTION CERTIFICATE (IF APPLICABLE)</td></tr>"
		"<tr><td>17</td><td>PROVIDENT FUND UAN (IF APPLICABLE)</td></tr>"
		"<tr><td>18</td><td>UPDATED CV</td></tr>"
		"<tr><td>19</td><td>PAN &amp; AADHAAR LINK (PROVIDE PROOF)</td></tr>"
		"</table>"
		"<p>We also will also need:</p><ul>"
		"<li>A digital photograph (non-passport) for the people directory on the website.</li>"
		"<li>A brief write-up (not more than 200 words) about yourself, covering your qualifications, your work experience, "
		"your research areas (if applicable), and your interests.</li></ul>"
		"<p>Please note:<br>The write-up should be shared in a WORD format and must be emailed by replying to this email at "
		"least 02 days prior to your date of joining.<br>Kindly find the reference link for the format below<br>"
		"<a href=\"https://www.nls.ac.in/people/anjali-varma/\">https://www.nls.ac.in/people/anjali-varma/</a></p>"
		"<p><b>Onboarding on to the ERP</b></p>"
		"<p>As a part of the onboarding process, we have sent you a link from people@nls.ac.in for updating your details on "
		"the ERP. Please fill in the details and upload the relevant documents at the earliest.</p>"
		"<p>On the day of joining{% if joining_date %} ({{ joining_date }}){% endif %}, please meet me on the "
		"{{ reporting_location or 'Ground Floor, Training Centre Room No. 004' }} at {{ reporting_time or '10:00 am' }}.</p>"
		"<p>Regards,<br>People and Culture Team<br>NLSIU, Bengaluru</p>",
	),
	# Workflow folder: 12. Intimation to IT-Facilities / Email.
	"IT & Facilities Intimation": (
		"New joiner: {{ candidate_name }}, {{ job_title }}",
		"<p>Dear Team,</p>"
		"<p>The following staff member is joining as indicated against their name. Kindly arrange for a laptop, create NLS "
		"email ID, and share the same.</p>"
		"<p>Name: {{ candidate_name }}<br>Designation: {{ job_title }}<br>Date of Joining: {{ joining_date }}<br>"
		"Email: {{ candidate_email }}<br>Mobile No. : {{ candidate_mobile }}</p>"
		"<p>Thanks!</p><p>Regards,<br>People and Culture Team<br>NLSIU, Bengaluru</p>",
	),
}

JOB_VARS = "job_title, job_code, department, vacancies, deadline, posting_link, job_link, recipient_name, contact_email"
CANDIDATE_VARS = "candidate_name, application_id, job_title, recipient_name, contact_email"

# (stage, event, label, when, template, recipients, automatic, enabled, variables)
EVENTS = [
	("Job & Advertisement", "green_sheet_approval", "Green Sheet awaiting approval", "A Pre-Recruitment Green Sheet reaches an approval step (also a bell notification).",
		"Green Sheet Approval Request", {"send_to_approvers": 1}, True, True, "doc_name, job_title, approver_label, link, recipient_name"),
	("Job & Advertisement", "job_advertised", "Advertisement live: Registrar's Office & Communications",
		"A job is advertised (workflow step 3: official notification, website and social media).",
		"Job Advertised Notice", {"roles": ["Pathways Registrar", "Pathways Communications"]}, True, True, JOB_VARS + ", notification_number"),
	("Job & Advertisement", "corrigendum_issued", "Corrigendum issued", "A corrigendum (e.g. a deadline extension) is issued.",
		"Corrigendum Notice", {"roles": ["Pathways Registrar", "Pathways Communications"]}, True, True, JOB_VARS + ", change, remarks"),
	("Job & Advertisement", "ad_closing_soon", "Advertisement closing within 24 hours", "Daily check, one day before the deadline (decide whether to extend).",
		"Advertisement Closing Soon", {"roles": ["Pathways Recruiter"]}, True, True, JOB_VARS + ", application_count"),
	("Applications", "application_received", "Application received (to candidate)", "A candidate submits an application.",
		"Application Acknowledgement", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS),
	("Applications", "candidate_portal_access", "Candidate portal login (to candidate)",
		"A candidate's first application: their portal account is created and the username (Candidate ID) and a temporary password are emailed.",
		"Candidate Portal Login", {"send_to_candidate": 1}, True, True, "candidate_name, candidate_id, username, temporary_password, login_link, contact_email"),
	("Screening & Shortlisting", "committee_assigned", "Shortlisting committee invitation", "A job's Shortlisting Committee is set up (one email per member).",
		"Shortlisting Committee Invitation", {"send_to_committee": 1}, True, True, JOB_VARS + ", application_count, ratio"),
	("Screening & Shortlisting", "candidate_not_eligible", "Regret: not eligible (to candidate)", "A candidate is marked not eligible. Off by default: regrets are usually sent together later.",
		"Regret Mail", {"send_to_candidate": 1}, True, False, CANDIDATE_VARS),
	("Screening & Shortlisting", "candidate_not_shortlisted", "Regret: not shortlisted (to candidate)", "The committee rejects a candidate at shortlisting. Off by default.",
		"Regret Mail", {"send_to_candidate": 1}, True, False, CANDIDATE_VARS),
	("Screening & Shortlisting", "shortlisting_regret", "Regret after screening (sent together)",
		"Sent from a job's Shortlisting card to every not-eligible or not-shortlisted candidate who has not had a regret yet.",
		"Regret Mail", {"send_to_candidate": 1}, False, True, CANDIDATE_VARS),
	("Screening & Shortlisting", "candidate_shortlisted", "Shortlisted (to candidate)", "The committee shortlists a candidate. Off by default: the interview invite usually follows.",
		"Shortlisted Notice", {"send_to_candidate": 1}, True, False, CANDIDATE_VARS),
	("Interviews", "selection_committee_assigned", "Selection committee invitation (to panellists)",
		"A job's Selection Committee is set up, or a panellist is added to it (workflow step 15).",
		"Selection Committee Invitation", {"send_to_approvers": 1}, True, True, JOB_VARS + ", interview_date, interview_time, panel, candidate_count"),
	("Interviews", "interview_invite_round1", "Interview invite: Round 1 / HR interaction", "Round 1 is scheduled (workflow step 13).",
		"Interview Invite (Round 1)", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", interview_date_time, meeting_link, meeting_platform, interview_location, rsvp_deadline, rsvp_link"),
	("Interviews", "interview_call_letter", "Interview call letter: final interview", "The final interview is scheduled (workflow steps 14-16).",
		"Interview Call Letter", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", track, interview_date, interview_day, interview_time, interview_mode, meeting_platform, meeting_link, interview_location, meeting_details, login_time, rsvp_link"),
	("Interviews", "interview_reminder", "Interview reminder (to candidate)", "Daily, the day before a scheduled interview.",
		"Interview Reminder", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", interview_date_time, meeting_link"),
	("Selection & Offer", "appointment_order", "Appointment order (to candidate)", "The signed appointment order is sent (workflow step 28).",
		"Appointment Order Covering Note", {"send_to_candidate": 1, "attach_record_files": 1}, False, True, CANDIDATE_VARS + ", acceptance_deadline, pnc_contacts"),
	("Selection & Offer", "regret_after_interview", "Regret after interview (to candidate)", "Interviewed candidates who were not selected (workflow step 32).",
		"Regret Mail", {"send_to_candidate": 1}, False, True, CANDIDATE_VARS),
	("Onboarding & Closure", "panel_thanks", "Thank you to panellists", "After the interviews (workflow step 33).",
		"Panel Thank You", {}, False, True, "job_title, recipient_name"),
	("Onboarding & Closure", "onboarding", "Onboarding documents (to new joiner)", "The candidate accepts the offer (workflow step 34).",
		"Onboarding Documents", {"send_to_candidate": 1}, False, True, CANDIDATE_VARS + ", joining_date, reporting_location, reporting_time"),
	("Onboarding & Closure", "it_facilities", "Intimation to IT & Facilities", "Joining is confirmed (laptop, NLS email ID).",
		"IT & Facilities Intimation", {"roles": ["Pathways IT Facilities"]}, False, True,
		"candidate_name, job_title, joining_date, candidate_email, candidate_mobile"),
]


def ensure_email_events():
	for name, (subject, response) in TEMPLATES.items():
		if not frappe.db.exists("Email Template", name):
			frappe.get_doc({"doctype": "Email Template", "name": name, "subject": subject, "response": response, "use_html": 1}).insert(
				ignore_permissions=True
			)

	for order, (stage, event, label, when, template, recipients, automatic, enabled, variables) in enumerate(EVENTS, start=1):
		if frappe.db.exists("Recruitment Email Rule", event):
			# Keep staff edits; only facts the code owns are refreshed.
			frappe.db.set_value(
				"Recruitment Email Rule",
				event,
				{"is_automatic": int(automatic), "trigger_description": when, "variables": variables, "stage": stage, "sort_order": order},
				update_modified=False,
			)
			continue
		if not frappe.db.exists("Email Template", template):
			continue
		frappe.get_doc(
			{
				"doctype": "Recruitment Email Rule",
				"event": event,
				"label": label,
				"stage": stage,
				"sort_order": order,
				"enabled": int(enabled),
				"is_automatic": int(automatic),
				"trigger_description": when,
				"email_template": template,
				"send_to_candidate": recipients.get("send_to_candidate", 0),
				"send_to_committee": recipients.get("send_to_committee", 0),
				"send_to_approvers": recipients.get("send_to_approvers", 0),
				"attach_record_files": recipients.get("attach_record_files", 0),
				"recipient_roles": [{"role": r} for r in recipients.get("roles", []) if frappe.db.exists("Role", r)],
				"variables": variables,
			}
		).insert(ignore_permissions=True)
