import frappe

PATHWAYS_ROLES = [
	"Pathways Admin",
	"Pathways Recruiter",
	"Pathways PNCO",
	"Pathways Director People Culture",
	"Pathways Dean Academics",
	"Pathways Dean Research",
	"Pathways Senior Manager Research",
	"Pathways CFO",
	"Pathways Registrar",
	"Pathways Vice Chancellor",
	"Pathways Shortlisting Committee Member",
	"Pathways Selection Committee Member",
	"Pathways Communications",
	"Pathways IT Facilities",
	"Pathways Candidate",
]


EMAIL_TEMPLATES = [
	{
		"name": "Application Acknowledgement",
		"subject": "Application Received: {{ job_title }}",
		"response": (
			"<p>Dear {{ candidate_name }},</p>"
			"<p>Thank you for applying for the position of <b>{{ job_title }}</b> at "
			"National Law School of India University (NLSIU), Bengaluru. "
			"Your application (ID: {{ application_id }}) has been received.</p>"
			"<p>Kind regards,<br>Recruitment Team<br>NLSIU, Bengaluru</p>"
		),
	},
	{
		"name": "Interview Invite (Round 1)",
		"subject": "Action Required : Interviews - {{ job_title }}",
		"response": (
			"<p>Dear Applicant,</p>"
			"<p>Greetings from National Law School of India University (NLSIU), Bengaluru!</p>"
			"<p>This is with reference to your interviews (Round 1) for the position "
			"{{ job_title }} at NLS. We are pleased to inform you that your application "
			"has been selected for the Round 1 interview. This round is scheduled on "
			"{{ interview_date_time }} via video conferencing.</p>"
			"<p>Meeting link: {{ meeting_link }}</p>"
			"<p>Please login into the meeting ten minutes before your start time. "
			"We request you to keep a two-hour window for the interview to factor for any delay.</p>"
			"<p>Please confirm your participation by replying to this email by {{ rsvp_deadline }}.</p>"
			"<p>Kind regards,<br>Recruitment Team<br>NLSIU, Bengaluru</p>"
		),
	},
	{
		"name": "Interview Call Letter",
		"subject": "Action Required : Interviews for the position of {{ job_title }}",
		"response": (
			"<p>Dear Applicant,</p>"
			"<p>Greetings from National Law School of India University (NLSIU), Bengaluru!</p>"
			"<p>We are pleased to inform you that your application has been shortlisted, "
			"and your interview is scheduled via video conferencing on {{ interview_date_time }}.</p>"
			"<p>Meeting details: {{ meeting_link }}</p>"
			"<p>Please login twenty minutes before your start time and please remain logged in. "
			"Please ensure that your camera and microphone are switched on when you enter the "
			"meeting room.</p>"
			"<p>Kind regards,<br>Recruitment Team<br>NLSIU, Bengaluru</p>"
		),
	},
	{
		"name": "Regret Mail",
		"subject": "Important: Update on your job application for {{ job_title }}",
		"response": (
			"<p>Dear Candidate,</p>"
			"<p>We have an update on your application for the position of {{ job_title }} "
			"at NLSIU Bengaluru.</p>"
			"<p>We regret to inform you that we will not be moving forward with your application. "
			"We truly appreciate the time and effort put in by you for your application.</p>"
			"<p>Please note that this decision is not a reflection of your abilities, and we "
			"encourage you to apply for positions that may/will come up in the future.</p>"
			"<p>Please keep a lookout on the website - https://www.nls.ac.in/news-and-events/work-with-us/</p>"
			"<p>Kind regards,<br>Recruitment Team<br>NLSIU, Bengaluru</p>"
		),
	},
	{
		"name": "Appointment Order Covering Note",
		"subject": "Appointment Letter - {{ job_title }}",
		"response": (
			"<p>Dear {{ candidate_name }},</p>"
			"<p>Greetings from National Law School of India University, Bengaluru!</p>"
			"<p>Please find attached the Appointment Letter as {{ job_title }} at NLSIU. "
			"Request you to confirm your acceptance and send a signed scanned copy of the "
			"appointment letter with a reply all to this email by {{ acceptance_deadline }}.</p>"
			"<p>Please also indicate your earliest date of joining in the same email.</p>"
			"<p>Regards,<br>Registrar's Office</p>"
		),
	},
	{
		"name": "Onboarding Email",
		"subject": "DOCUMENTS TO BE SUBMITTED",
		"response": (
			"<p>Dear {{ candidate_name }},</p>"
			"<p>We are looking forward to welcoming you to NLSIU!</p>"
			"<p>On the day of joining, kindly bring the softcopy and photocopy of the required "
			"documents as per the checklist shared with you.</p>"
			"<p>We will also need a digital photograph for the people directory on the website, "
			"and a brief write-up (not more than 200 words) about yourself, to be emailed at "
			"least 2 days prior to your date of joining.</p>"
			"<p>On the day of joining, please meet at {{ reporting_location }} at {{ reporting_time }}.</p>"
			"<p>Regards,<br>People and Culture Team<br>NLSIU, Bengaluru</p>"
		),
	},
	{
		"name": "IT Facilities Intimation",
		"subject": "New Staff Joining - {{ employee_name }}",
		"response": (
			"<p>Dear Team,</p>"
			"<p>The following staff member is joining as indicated against their name. "
			"Kindly arrange for a laptop, create NLS email ID, and share the same.</p>"
			"<p>Name: {{ employee_name }}<br>"
			"Designation: {{ designation }}<br>"
			"Date of Joining: {{ date_of_joining }}<br>"
			"Personal Email: {{ personal_email }}<br>"
			"Mobile No.: {{ mobile_number }}</p>"
			"<p>Thanks!<br>Regards,</p>"
		),
	},
	{
		"name": "Email to Shortlisting Committee",
		"subject": "Shortlisting Request: {{ job_title }}",
		"response": (
			"<p>Dear Committee Member,</p>"
			"<p>Thank you for agreeing to be a part of the shortlisting committee for "
			"{{ job_title }}. We have received {{ application_count }} responses for the advertisement.</p>"
			"<ul>"
			"<li>1:{{ shortlisting_ratio }} candidates, if available, need to be shortlisted for interviews.</li>"
			"<li>Please first check whether the candidate is eligible for the position. "
			"Note the reason for ineligibility. Ineligible candidates need not be assigned a score.</li>"
			"<li>Please score the candidates in the form provided. Please arrive at a common score "
			"as a panel, not individually.</li>"
			"<li>Please keep the shortlist confidential until candidates have been invited for interview.</li>"
			"</ul>"
			"<p><b>Important</b> — While shortlisting for interviews, please ensure that the "
			"candidates shortlisted come from diverse backgrounds.</p>"
			"<p>We request you to complete the shortlisting by {{ shortlisting_deadline }}.</p>"
			"<p>Thank you for your time and effort.</p>"
		),
	},
	{
		"name": "Document Resubmission Request",
		"subject": "Action Required: Document Resubmission - {{ document_name }}",
		"response": (
			"<p>Dear {{ candidate_name }},</p>"
			"<p>We reviewed the document you submitted for <b>{{ document_name }}</b> and it could "
			"not be accepted for the following reason:</p>"
			"<p><i>{{ rejection_reason }}</i></p>"
			"<p>Please log in to your application portal and upload a corrected copy at your earliest "
			"convenience.</p>"
			"<p>Regards,<br>People and Culture Team<br>NLSIU, Bengaluru</p>"
		),
	},
	{
		"name": "Interview Reminder",
		"subject": "Reminder: Your interview is tomorrow",
		"response": (
			"<p>Dear Candidate,</p>"
			"<p>This is a reminder that your interview is scheduled for tomorrow. "
			"Please refer to your earlier interview invitation email for the date, time and "
			"meeting details.</p>"
			"<p>Kind regards,<br>Recruitment Team<br>NLSIU, Bengaluru</p>"
		),
	},
	{
		"name": "Panelist Thanks",
		"subject": "Thank You for Serving on the Selection Committee",
		"response": (
			"<p>Dear {{ panelist_name }},</p>"
			"<p>On behalf of NLSIU, thank you for your time and effort in serving on the "
			"Selection Committee for {{ job_title }}. Your contribution is greatly appreciated.</p>"
			"<p>Regards,<br>Recruitment Team<br>NLSIU, Bengaluru</p>"
		),
	},
]


def after_install():
	create_roles()
	create_email_templates()


def create_roles():
	for role_name in PATHWAYS_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = 0 if role_name == "Pathways Candidate" else 1
		role.insert(ignore_permissions=True)
	frappe.db.commit()


def create_email_templates():
	for template in EMAIL_TEMPLATES:
		if frappe.db.exists("Email Template", template["name"]):
			continue
		doc = frappe.new_doc("Email Template")
		doc.name = template["name"]
		doc.subject = template["subject"]
		doc.response = template["response"]
		doc.use_html = 1
		doc.insert(ignore_permissions=True)
	frappe.db.commit()


