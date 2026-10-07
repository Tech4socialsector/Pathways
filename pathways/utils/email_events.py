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
	"Shortlisting Committee Invitation": (
		"Shortlisting committee: {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>Thank you for agreeing to be a part of the shortlisting committee for <b>{{ job_title }}</b>. "
		"We have received {{ application_count }} responses for the advertisement.</p>"
		"<p>Please note the essential steps to be followed in shortlisting candidates for interview:</p><ul>"
		"<li>1:{{ ratio }} candidates, if available, need to be shortlisted for interviews.</li>"
		"<li>Please first check whether the candidate is eligible for the position. Note the reason for ineligibility; "
		"ineligible candidates need not be assigned a score.</li>"
		"<li>Please score the candidates in Pathways. Arrive at a common score as a panel.</li>"
		"<li>Please keep the shortlist confidential until the candidates have been invited for interview by the PnC team.</li></ul>"
		"<p><b>Important</b> - While shortlisting, please ensure that the candidates shortlisted come from diverse backgrounds. "
		"At NLSIU we value diversity and believe it enriches the environment, fosters inclusion, and strengthens our community.</p>"
		"<p>The applications and documents are here: <a href=\"{{ job_link }}\">{{ job_link }}</a>"
		"{% if deadline %}<br>Please complete the shortlisting by {{ deadline }}.{% endif %}</p>" + SIGN_OFF,
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
	"Onboarding Documents": (
		"DOCUMENTS TO BE SUBMITTED",
		"<p>Dear {{ candidate_name }},</p><p>We are looking forward to welcoming you to NLSIU!</p>"
		"<p>On the day of joining, kindly bring the softcopy and photocopy of: PAN (mandatory), Aadhaar (mandatory), "
		"digital photograph (mandatory), passport (optional), copy of the signed appointment order (mandatory), Class X and XII "
		"certificates (mandatory), graduation certificate and transcripts (mandatory), post-graduation certificate and "
		"transcripts (if applicable), latest payslips (mandatory), relieving letter (mandatory), no objection certificate "
		"(if applicable), Provident Fund UAN (if applicable), updated CV, and proof of PAN-Aadhaar link.</p>"
		"<p>We will also need a digital photograph (non-passport) for the people directory on the website, and a brief "
		"write-up (not more than 200 words) about yourself in Word format, emailed at least 2 days before your date of joining.</p>"
		+ SIGN_OFF,
	),
	"IT & Facilities Intimation": (
		"New joiner: {{ candidate_name }}, {{ job_title }}",
		"<p>Dear Team,</p>"
		"<p>The following staff member is joining as indicated against their name. Kindly arrange for a laptop, create an "
		"NLS email ID, and share the same.</p>"
		"<p>Name: {{ candidate_name }}<br>Designation: {{ job_title }}<br>Date of Joining: {{ joining_date }}<br>"
		"Email: {{ candidate_email }}<br>Mobile No.: {{ candidate_mobile }}</p><p>Thanks!</p>" + SIGN_OFF,
	),
}

JOB_VARS = "job_title, job_code, department, vacancies, deadline, posting_link, job_link, recipient_name"
CANDIDATE_VARS = "candidate_name, application_id, job_title, recipient_name"

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
	("Screening & Shortlisting", "committee_assigned", "Shortlisting committee invitation", "A job's Shortlisting Committee is set up (one email per member).",
		"Shortlisting Committee Invitation", {"send_to_committee": 1}, True, True, JOB_VARS + ", application_count, ratio"),
	("Screening & Shortlisting", "candidate_not_eligible", "Regret: not eligible (to candidate)", "A candidate is marked not eligible. Off by default: regrets are usually sent together later.",
		"Regret Mail", {"send_to_candidate": 1}, True, False, CANDIDATE_VARS),
	("Screening & Shortlisting", "candidate_not_shortlisted", "Regret: not shortlisted (to candidate)", "The committee rejects a candidate at shortlisting. Off by default.",
		"Regret Mail", {"send_to_candidate": 1}, True, False, CANDIDATE_VARS),
	("Screening & Shortlisting", "candidate_shortlisted", "Shortlisted (to candidate)", "The committee shortlists a candidate. Off by default: the interview invite usually follows.",
		"Shortlisted Notice", {"send_to_candidate": 1}, True, False, CANDIDATE_VARS),
	("Interviews", "interview_invite_round1", "Interview invite: Round 1 / HR interaction", "Round 1 is scheduled (workflow step 13).",
		"Interview Invite (Round 1)", {"send_to_candidate": 1}, False, True, CANDIDATE_VARS + ", interview_date_time, meeting_link, rsvp_deadline"),
	("Interviews", "interview_call_letter", "Interview call letter: final interview", "The final interview is scheduled (workflow steps 14-16).",
		"Interview Call Letter", {"send_to_candidate": 1}, False, True, CANDIDATE_VARS + ", interview_date_time, meeting_link"),
	("Interviews", "interview_reminder", "Interview reminder (to candidate)", "Daily, the day before a scheduled interview.",
		"Interview Reminder", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", interview_date_time, meeting_link"),
	("Selection & Offer", "appointment_order", "Appointment order (to candidate)", "The signed appointment order is sent (workflow step 28).",
		"Appointment Order Covering Note", {"send_to_candidate": 1, "attach_record_files": 1}, False, True, CANDIDATE_VARS + ", acceptance_deadline"),
	("Selection & Offer", "regret_after_interview", "Regret after interview (to candidate)", "Interviewed candidates who were not selected (workflow step 32).",
		"Regret Mail", {"send_to_candidate": 1}, False, True, CANDIDATE_VARS),
	("Onboarding & Closure", "panel_thanks", "Thank you to panellists", "After the interviews (workflow step 33).",
		"Panel Thank You", {}, False, True, "job_title, recipient_name"),
	("Onboarding & Closure", "onboarding", "Onboarding documents (to new joiner)", "The candidate accepts the offer (workflow step 34).",
		"Onboarding Documents", {"send_to_candidate": 1}, False, True, CANDIDATE_VARS + ", joining_date"),
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
