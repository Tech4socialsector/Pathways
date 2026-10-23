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
		"<p><b>Greetings from National Law School of India University (NLSIU), Bangalore!</b></p>"
		"{% if updated %}<p style=\"padding:10px 12px;background:#FFF4E5;border-left:3px solid #D97706\"><b>Please note: the interview details have changed. "
		"This email replaces our earlier invitation.</b>{% if change_note %}<br>{{ change_note }}{% endif %}</p>{% endif %}"
		"<p>This is with reference to your interviews (Round 1) for the position <b>{{ job_title }} at NLS.</b> We are pleased to "
		"inform you that your application has been selected for the <b>Round 1 interview</b>. <b>This round is scheduled on "
		"{{ interview_date_time }}{% if interview_location %} in person at {{ interview_location }}{% else %} via video conferencing{% endif %}.</b></p>"
		"{% if interview_location %}<ol>"
		"<li>Please arrive <b>ten minutes</b> before your start time at {{ interview_location }}.</li>"
		"{% else %}<p><b>Please find below the {{ meeting_platform or 'Teams' }} link for the new meeting:</b><br>"
		"<a href=\"{{ meeting_link }}\">{{ meeting_link }}</a></p><ol>"
		"<li>Please login into the {{ meeting_platform or 'Teams' }} meeting <b>ten minutes</b> before your start time and please "
		"remain logged in. You will be admitted into the {{ meeting_platform or 'Teams' }} call once the panel is ready.</li>{% endif %}"
		"<li>While our earnest attempt is to bring each candidate into the interview room as per schedule, we request you to "
		"bear with us if there is a delay.<br><b>IMPORTANT - We request you to keep a two-hour window for the interview to "
		"factor for any delay.</b></li>"
		"<li>If you face any technical glitches, please be assured that our team will reach out to you. You can also email us "
		"at {{ contact_email or 'recruitment@nls.ac.in' }}.</li></ol>"
		"<p><b>Please confirm your participation on the candidate portal{% if rsvp_deadline %} by {{ rsvp_deadline }}{% endif %}.</b>"
		"</p>"
		"{% if rsvp_respond_link %}<table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" style=\"margin:16px 0\"><tr>"
		"<td style=\"background:#920C24;border-radius:6px\"><a href=\"{{ rsvp_respond_link }}\" style=\"display:inline-block;padding:11px 22px;color:#ffffff;font-weight:bold;text-decoration:none\">Click here to respond</a></td>"
		"</tr></table>"
		"<p style=\"font-size:12px;color:#666\">The button opens the NLSIU candidate portal. Sign in with your Candidate ID and password to accept or decline the interview.</p>"
		"{% endif %}" + SIGN_OFF,
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
	# No template in the workflow folder: an interview is called off.
	"Interview Cancelled": (
		"Update: your interview for {{ job_title }}",
		"<p>Dear Applicant,</p>"
		"<p>Greetings from National Law School of India University (NLSIU), Bangalore!</p>"
		"<p>We regret to inform you that your {{ interview_round }} for the position of {{ job_title }}, scheduled on "
		"<b>{{ interview_date_time }}</b>, has been cancelled.{% if reason %} {{ reason }}{% endif %}</p>"
		"<p>The Recruitment Team will get in touch with you about the next steps. You can also email us at "
		"{{ contact_email or 'recruitment@nls.ac.in' }}.</p>" + SIGN_OFF,
	),
	# Workflow folder: 6. Final Interview / Interview Call Letter.
	"Interview Call Letter": (
		"Action Required : Interviews for the position of {{ job_title }}",
		"<p>Dear Applicant,</p>"
		"<p>Greetings from National Law School of India University (NLSIU), Bangalore!</p>"
		"{% if updated %}<p style=\"padding:10px 12px;background:#FFF4E5;border-left:3px solid #D97706\"><b>Please note: the interview details have changed. "
		"This email replaces our earlier invitation.</b>{% if change_note %}<br>{{ change_note }}{% endif %}</p>{% endif %}"
		"<p>This is with reference to your application for the position of <b>{{ job_title }}</b> in our institution.</p>"
		"<p>We are pleased to inform you that your application has been shortlisted, and your interview is scheduled "
		"{% if interview_location %}<b>in person on:</b>{% else %}via video <b>conferencing on:</b>{% endif %}</p>"
		"<p><b>Date - {{ interview_date }}<br>Day - {{ interview_day }}<br>Time - {{ interview_time }}<br>"
		"Mode - {{ interview_mode or 'Online' }}{% if interview_location %}<br>Venue - {{ interview_location }}{% endif %}</b></p>"
		"{% if track == 'Faculty' %}<p>The interview will be in 2 parts:</p><ol>"
		"<li>A talk by you on your pedagogical approach to teaching, with at least one example (approximately 3 to 5 minutes). "
		"Please note that due to a paucity of time, slide presentations are not possible.</li>"
		"<li>A discussion with the Selection Committee (approximately 10 minutes).</li></ol>{% endif %}"
		"{% if interview_location %}<p><b>Please note:</b></p><ol>"
		"<li>Please report at {{ interview_location }} <b>twenty minutes</b>{% if login_time %} <b>({{ login_time }})</b>{% endif %} before your "
		"start time. You will be called in once the Committee is ready.</li>"
		"{% else %}<p>Please find the details of the meeting ID and password for the {{ meeting_platform or 'Teams' }} call:<br>"
		"<b><a href=\"{{ meeting_link }}\">{{ meeting_link }}</a>{% if meeting_details %}<br>{{ meeting_details }}{% endif %}</b></p>"
		"<p><b>Please note:</b></p><ol>"
		"<li>Please login into the {{ meeting_platform or 'Teams' }} meeting <b>twenty minutes</b>{% if login_time %} <b>({{ login_time }})</b>{% endif %} "
		"before your start time and please remain logged in. You will be admitted into the {{ meeting_platform or 'Teams' }} call once the Committee is ready. "
		"Please ensure that your camera and microphone are switched on when you enter the meeting room.</li>{% endif %}"
		"<li>While our earnest attempt is to bring each candidate into the interview room as per schedule, we request you to "
		"bear with us if there is a delay.</li>"
		"<li>If you face any technical glitches, please be assured that our recruitment team will reach out to you. You can "
		"also email us at {{ contact_email or 'recruitment@nls.ac.in' }}.</li></ol>"
		"{% if rsvp_respond_link %}<p><b>Please confirm your attendance on the candidate portal{% if rsvp_deadline %} by {{ rsvp_deadline }}{% endif %}.</b></p>{% endif %}"
		"{% if rsvp_respond_link %}<table role=\"presentation\" cellpadding=\"0\" cellspacing=\"0\" style=\"margin:16px 0\"><tr>"
		"<td style=\"background:#920C24;border-radius:6px\"><a href=\"{{ rsvp_respond_link }}\" style=\"display:inline-block;padding:11px 22px;color:#ffffff;font-weight:bold;text-decoration:none\">Click here to respond</a></td>"
		"</tr></table>"
		"<p style=\"font-size:12px;color:#666\">The button opens the NLSIU candidate portal. Sign in with your Candidate ID and password to accept or decline the interview.</p>"
		"{% endif %}"
		# The call letter signs off from Bangalore, as in the folder's letter.
		"<p>Kind regards,<br>Recruitment Team<br>NLSIU, Bangalore</p>"
		"<p><b>General Instructions:</b></p><ol>"
		"<li>Ensure your room is well-illuminated and free of any background/external noise.</li>"
		"<li>Ensure your computer's mic and camera are functioning well, with the background being clear.</li>"
		"<li>Test your internet speed/stability, keep a backup.</li></ol>",
	),
	# Internal hand-offs on an appointment order (workflow steps 26-27).
	"Appointment Order Review Request": (
		"Appointment order for review: {{ candidate_name }} ({{ designation or job_title }})",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>The draft appointment order <b>{{ offer_name }}</b> for <b>{{ candidate_name }}</b> "
		"({{ designation or job_title }}) is ready for your review.</p>"
		"<p>Please check the letter and either approve it for the Registrar's signature or return it for changes: "
		"<a href=\"{{ link }}\">{{ link }}</a></p>" + SIGN_OFF,
	),
	"Appointment Order Signature Request": (
		"Appointment order for signature: {{ candidate_name }} ({{ designation or job_title }})",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>The appointment order <b>{{ offer_name }}</b> for <b>{{ candidate_name }}</b> "
		"({{ designation or job_title }}) has been reviewed and is ready for your signature.</p>"
		"<p>Open it to preview the letter and sign: <a href=\"{{ link }}\">{{ link }}</a></p>" + SIGN_OFF,
	),
	"Appointment Order Returned": (
		"Appointment order returned for changes: {{ candidate_name }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>The appointment order <b>{{ offer_name }}</b> for <b>{{ candidate_name }}</b> "
		"({{ designation or job_title }}) has been returned to draft for changes.</p>"
		"{% if remarks %}<p>Remarks: <i>{{ remarks }}</i></p>{% endif %}"
		"<p><a href=\"{{ link }}\">{{ link }}</a></p>" + SIGN_OFF,
	),
	# Workflow folder: 10. Appointment Order email / Letter to Candidate.
	"Appointment Order Covering Note": (
		"Appointment Letter - {{ job_title }}",
		"<p>Dear {{ candidate_name }},</p>"
		"<p>Greetings from the National Law School of India University, Bangalore!</p>"
		"<p>Please find attached the Appointment Letter as {{ job_title }} at NLSIU.</p>"
		"<p><b>Please accept or decline the offer by {{ acceptance_deadline }}</b> on the NLSIU Careers portal"
		"{% if portal_link %}: <a href=\"{{ portal_link }}\">{{ portal_link }}</a>{% endif %}. "
		"Log in with the email or Candidate ID you applied with, open this application and, under <b>Appointment order</b>, "
		"choose your date of joining and click <b>Accept offer</b> (or <b>Decline</b>). Please also upload a signed scanned copy "
		"of the appointment letter there.</p>"
		"<p>If you cannot use the portal, reply to this email with your decision, your earliest date of joining and the signed "
		"copy, and we will record it for you.</p>"
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
		"<tr><td style=\"padding:4px 16px 4px 0;color:#555\">Log in with</td><td>your email address"
		"{% if login_mobile %}, your mobile number <b>{{ login_mobile }}</b>{% endif %} or your Candidate ID <b>{{ username }}</b></td></tr>"
		"<tr><td style=\"padding:4px 16px 4px 0;color:#555\">Temporary password</td><td><b>{{ temporary_password }}</b></td></tr>"
		"</table>"
		"<p>You will be asked to set your own password the first time you log in. "
		"Please do not share these details with anyone.</p>" + SIGN_OFF,
	),
	"Green Sheet Approval Request": (
		"Approval needed: Green Sheet for {{ job_title }}",
		"<p>Dear {{ recipient_name }},</p>"
		"<p>The {{ doc_type or 'Pre-Recruitment Green Sheet' }} <b>{{ doc_name }}</b> for <b>{{ job_title }}</b> is awaiting your approval "
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
		"{% if portal_link %}<p><b>Upload your joining documents</b><br>Please also upload a scanned copy of each document above on the "
		"candidate portal, so that we can verify them before you join: <a href=\"{{ portal_link }}\">{{ portal_link }}</a></p>{% endif %}"
		"<p>On the day of joining{% if joining_date %} ({{ joining_date }}){% endif %}, please meet me on the "
		"{{ reporting_location or 'Ground Floor, Training Centre Room No. 004' }} at {{ reporting_time or '10:00 am' }}.</p>"
		"<p>Regards,<br>People and Culture Team<br>NLSIU, Bengaluru</p>",
	),
	# Workflow folder: 12. Intimation to IT-Facilities / Email.
	"IT & Facilities Intimation": (
		"New joiner: {{ candidate_name }}, {{ job_title }}",
		"<p>Dear Team,</p>"
		"{% if updated %}<p style=\"padding:10px 12px;background:#FFF4E5;border-left:3px solid #D97706\"><b>Please note: the joining "
		"details have changed. This email replaces our earlier intimation.</b></p>{% endif %}"
		"<p>The following staff member is joining as indicated against their name. Kindly arrange for a laptop, create NLS "
		"email ID, and share the same.</p>"
		"<p>Name: {{ candidate_name }}<br>Designation: {{ job_title }}<br>Date of Joining: {{ joining_date }}<br>"
		"Email: {{ candidate_email }}<br>Mobile No. : {{ candidate_mobile }}</p>"
		"{% if request_link %}<p>Please record the laptop, the NLS email ID and the access card / seating on Pathways: "
		"<a href=\"{{ request_link }}\">{{ request_link }}</a></p>{% endif %}"
		"<p>Thanks!</p><p>Regards,<br>People and Culture Team<br>NLSIU, Bengaluru</p>",
	),
}

TEMPLATES["Panel Documents Shared"] = (
	"Candidate documents for {{ job_title }}",
	"<p>Dear {{ recipient_name }},</p>"
	"<p>The recruitment team has shared candidate documents with you for the position of <b>{{ job_title }}</b>, "
	"for your review ahead of the interview.</p>"
	"<ul>{% for c in candidates %}<li><b>{{ c.name }}</b> ({{ c.application_id }}): {{ c.documents }}</li>{% endfor %}</ul>"
	"{% if note %}<p><b>Note from {{ shared_by }}:</b> {{ note }}</p>{% endif %}"
	"<p>Please log in to view them: <a href=\"{{ documents_link }}\">{{ documents_link }}</a></p>"
	"<p>Please keep these documents confidential and do not share them outside the panel.</p>" + SIGN_OFF,
)

# No template in the workflow folder (step 13): the two people taking a
# Round 1 / HR interaction, with the candidate, the link and the sheet.
TEMPLATES["HR Assessor Assignment"] = (
	"Round 1 (HR interaction): {{ candidate_name }}, {{ job_title }}",
	"<p>Dear {{ recipient_name }},</p>"
	"{% if updated %}<p style=\"padding:10px 12px;background:#FFF4E5;border-left:3px solid #D97706\"><b>Please note: the interview details "
	"have changed. This email replaces the earlier one.</b></p>{% endif %}"
	"<p>You have been assigned as an HR assessor for the <b>Round 1 (HR interaction)</b> of <b>{{ candidate_name }}</b> "
	"({{ application_id }}) for the position of <b>{{ job_title }}</b>.</p>"
	"<p><b>When:</b> {{ interview_date_time }}<br>"
	"{% if interview_location %}<b>Where:</b> {{ interview_location }}{% else %}<b>{{ meeting_platform or 'Meeting' }} link:</b> "
	"{% if meeting_link %}<a href=\"{{ meeting_link }}\">{{ meeting_link }}</a>{% else %}to follow{% endif %}{% endif %}</p>"
	"<p>The candidate's CV and statement of purpose, and the HR assessment sheet to fill after the interaction, are on Pathways: "
	"<a href=\"{{ assessment_link }}\">{{ assessment_link }}</a></p>"
	"<p>Please record your scores, your recommendation (recommend for the final interview, hold or not recommended) and a short "
	"HR interaction note, including the candidate's salary expectation and notice period.</p>" + SIGN_OFF,
)

# Workflow step 16: job-level files for the panel (notification, panel
# details, assessment sheets, shortlisting note, HR notes, schedule).
TEMPLATES["Panel Job Files Shared"] = (
	"Interview files for {{ job_title }}",
	"<p>Dear {{ recipient_name }},</p>"
	"<p>The recruitment team has shared the following files with you for the interviews for the position of <b>{{ job_title }}</b>:</p>"
	"<ul>{% for f in files %}<li>{{ f }}</li>{% endfor %}</ul>"
	"{% if note %}<p><b>Note from {{ shared_by }}:</b> {{ note }}</p>{% endif %}"
	"<p>Please log in to view them: <a href=\"{{ documents_link }}\">{{ documents_link }}</a></p>"
	"<p>Please keep these files confidential and do not share them outside the panel.</p>" + SIGN_OFF,
)

# Workflow folder: 9. Regret Mails / Regret Email Template. Same wording as
# "Regret Mail" today, but its own template so the post-interview regret can
# be edited without changing the screening regret.
TEMPLATES["Regret After Interview"] = (
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
)

# Workflow folder: 7. Reference Checks forms (the covering text of the
# Admin and Research forms). Sent to the referee, who is not a Pathways user.
TEMPLATES["Reference Check Request"] = (
	"NLSIU Reference Check | {{ candidate_name }}",
	"<p>Dear {{ referee_name }},</p>"
	"<p>Greetings from National Law School of India University (NLSIU), Bangalore!</p>"
	"<p>I am reaching out to you in connection with a reference check. An applicant to our institution, "
	"<b>{{ candidate_name }}</b>, has given your reference to us when applying for the post of <b>{{ job_title }}</b>. "
	"Your insights and feedback would greatly assist us in making an informed hiring decision. We would appreciate it "
	"if you could spare a few minutes to answer a few questions.</p>"
	"<p><a href=\"{{ form_link }}\">Open the reference check form</a></p>"
	"<p>We would be grateful if you can share your feedback by <b>{{ expires_on }}</b>, after which the link stops working. "
	"Your responses are kept confidential and are not shared with the candidate.</p>"
	"<p>Thank you in advance for your time, and we greatly appreciate your support in our hiring process.</p>" + SIGN_OFF,
)
TEMPLATES["Reference Check Reminder"] = (
	"Reminder: NLSIU Reference Check | {{ candidate_name }}",
	"<p>Dear {{ referee_name }},</p>"
	"<p>This is a gentle reminder about the reference check for <b>{{ candidate_name }}</b>, who has applied for the post of "
	"<b>{{ job_title }}</b> at NLSIU. We would be grateful for your feedback.</p>"
	"<p><a href=\"{{ form_link }}\">Open the reference check form</a></p>"
	"<p>The link works until <b>{{ expires_on }}</b>. Your responses are kept confidential and are not shared with the candidate.</p>"
	"<p>Thank you for your time.</p>" + SIGN_OFF,
)
TEMPLATES["Reference Check Received"] = (
	"Reference received: {{ candidate_name }}, {{ job_title }}",
	"<p>Dear {{ recipient_name }},</p>"
	"<p><b>{{ referee_name }}</b> has submitted the reference check for <b>{{ candidate_name }}</b> "
	"({{ application_id }}, {{ job_title }}).</p>"
	"<p>View the responses on the application's References panel: <a href=\"{{ application_link }}\">{{ application_link }}</a></p>" + SIGN_OFF,
)
REFERENCE_VARS = "candidate_name, job_title, referee_name, form_link, expires_on, contact_email"

# No template in the workflow folder: a joining document was not accepted.
TEMPLATES["Document Resubmission Request"] = (
	"Action Required: Document Resubmission - {{ document_name }}",
	"<p>Dear {{ candidate_name }},</p>"
	"<p>We reviewed the document you submitted for <b>{{ document_name }}</b> and it could not be accepted for the "
	"following reason:</p>"
	"<p><i>{{ rejection_reason }}</i></p>"
	"<p>Please upload a corrected copy on the candidate portal at your earliest convenience"
	"{% if portal_link %}: <a href=\"{{ portal_link }}\">{{ portal_link }}</a>{% endif %}.</p>"
	"<p>Regards,<br>People and Culture Team<br>NLSIU, Bengaluru</p>",
)
# No template in the workflow folder: IT & Facilities have set up a new joiner.
TEMPLATES["IT & Facilities Completed"] = (
	"IT & Facilities ready: {{ candidate_name }}, {{ job_title }}",
	"<p>Dear {{ recipient_name }},</p>"
	"<p>IT &amp; Facilities have completed the set-up for <b>{{ candidate_name }}</b> ({{ job_title }}), joining on "
	"<b>{{ joining_date }}</b>.</p>"
	"<p>{% if official_email %}Official email ID: <b>{{ official_email }}</b><br>{% endif %}Completed by: {{ completed_by }}</p>"
	"{% if joining_link %}<p><a href=\"{{ joining_link }}\">Open the joining in Pathways</a></p>{% endif %}" + SIGN_OFF,
)

# Workflow step 3: approval -> official notification (no template in the folder).
TEMPLATES["Official Notification Request"] = (
	"Action required: official notification for {{ job_title }}",
	"<p>Dear {{ recipient_name }},</p>"
	"<p>The Pre-Recruitment Green Sheet{% if green_sheet %} ({{ green_sheet }}){% endif %} for <b>{{ job_title }}</b>"
	"{% if department %} ({{ department }}){% endif %} has been approved.</p>"
	"<p>Please convert the draft advertisement into the official notification and publish it on the NLSIU website, "
	"LinkedIn and Indeed. Once it is out, please record the notification number, the official link and where it was "
	"published on the job page in Pathways (Notification &amp; Corrigenda, and Publishing).</p>"
	"<ul>{% if jd_link %}<li>Job description / draft notice: <a href=\"{{ jd_link }}\">{{ jd_link }}</a></li>{% endif %}"
	"<li>Job page: <a href=\"{{ job_link }}\">{{ job_link }}</a></li>"
	"{% if deadline %}<li>Application deadline: {{ deadline }}</li>{% endif %}</ul>" + SIGN_OFF,
)
# Workflow step 6: the ad has closed, take it down.
TEMPLATES["Advertisement Closed"] = (
	"Advertisement closed: {{ job_title }}",
	"<p>Dear {{ recipient_name }},</p>"
	"<p>The advertisement for <b>{{ job_title }}</b>{% if department %} ({{ department }}){% endif %} has closed"
	"{% if deadline %} (deadline {{ deadline }}){% endif %}. {{ application_count }} application(s) were received.</p>"
	"<p>Please take the advertisement down from the NLSIU website and the job portals"
	"{% if published_links %}:</p><ul>{% for l in published_links %}<li>{{ l.label }}: <a href=\"{{ l.url }}\">{{ l.url }}</a></li>{% endfor %}</ul>"
	"{% else %}.</p>{% endif %}"
	"<p>Job page: <a href=\"{{ job_link }}\">{{ job_link }}</a></p>" + SIGN_OFF,
)
# Workflow step 7: a colleague is tagged on a job.
TEMPLATES["Colleague Tagged on Job"] = (
	"You have been given access to {{ job_title }} on Pathways",
	"<p>Dear {{ recipient_name }},</p>"
	"<p>{{ tagged_by }} has shared the recruitment for <b>{{ job_title }}</b>{% if department %} ({{ department }}){% endif %} "
	"with you on Pathways. You can now read its applications and the candidates' documents.</p>"
	"{% if access_note %}<p><b>Note:</b> {{ access_note }}</p>{% endif %}"
	"<p>Applications: <a href=\"{{ applications_link }}\">{{ applications_link }}</a><br>"
	"Job page: <a href=\"{{ job_link }}\">{{ job_link }}</a></p>"
	"<p>Please keep the candidates' information confidential.</p>" + SIGN_OFF,
)

JOB_VARS = "job_title, job_code, department, vacancies, deadline, posting_link, job_link, recipient_name, contact_email"
CANDIDATE_VARS = "candidate_name, application_id, job_title, recipient_name, contact_email"
OFFER_VARS = "offer_name, candidate_name, job_title, designation, status, link, recipient_name"

# (stage, event, label, when, template, recipients, automatic, enabled, variables)
EVENTS = [
	("Job & Advertisement", "green_sheet_approval", "Green Sheet awaiting approval", "A Pre-Recruitment or Post-Interview (selection) Green Sheet, or any other approvable document, reaches an approval step (also a bell notification).",
		"Green Sheet Approval Request", {"send_to_approvers": 1}, True, True, "doc_name, doc_type, job_title, approver_label, link, recipient_name"),
	("Job & Advertisement", "notification_requested", "Green Sheet approved: prepare the official notification",
		"The Pre-Recruitment Green Sheet is fully approved: the Registrar's Office and Communications convert the draft into the official notification (workflow step 3).",
		"Official Notification Request", {"roles": ["Pathways Registrar", "Pathways Communications"]}, True, True, JOB_VARS + ", green_sheet, jd_link, track"),
	("Job & Advertisement", "job_advertised", "Advertisement live: Registrar's Office & Communications",
		"A job is advertised (workflow step 3: official notification, website and social media).",
		"Job Advertised Notice", {"roles": ["Pathways Registrar", "Pathways Communications"]}, True, True, JOB_VARS + ", notification_number"),
	("Job & Advertisement", "corrigendum_issued", "Corrigendum issued", "A corrigendum (e.g. a deadline extension) is issued.",
		"Corrigendum Notice", {"roles": ["Pathways Registrar", "Pathways Communications"]}, True, True, JOB_VARS + ", change, remarks"),
	("Job & Advertisement", "ad_closing_soon", "Advertisement closing within 24 hours", "Daily check, one day before the deadline (decide whether to extend).",
		"Advertisement Closing Soon", {"roles": ["Pathways Recruiter"]}, True, True, JOB_VARS + ", application_count"),
	("Job & Advertisement", "ad_closed", "Advertisement closed: take the ad down",
		"A job's deadline passes and it closes (hourly check), or it is closed by hand (workflow step 6). Its notification is closed too.",
		"Advertisement Closed", {"roles": ["Pathways Communications", "Pathways Recruiter"]}, True, True, JOB_VARS + ", application_count, published_links"),
	("Job & Advertisement", "colleague_tagged", "Colleague tagged on a job",
		"Someone is added to a job's \"Shared with\" list and can now read its applications and documents (workflow step 7).",
		"Colleague Tagged on Job", {"send_to_approvers": 1}, True, True, JOB_VARS + ", tagged_by, access_note, applications_link"),
	("Applications", "application_received", "Application received (to candidate)", "A candidate submits an application.",
		"Application Acknowledgement", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS),
	("Applications", "candidate_portal_access", "Candidate portal login (to candidate)",
		"A candidate's first application: their portal account is created and how to log in (email, mobile number or Candidate ID) and a temporary password are emailed.",
		"Candidate Portal Login", {"send_to_candidate": 1}, True, True, "candidate_name, candidate_id, username, login_mobile, temporary_password, login_link, contact_email"),
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
	("Interviews", "panel_documents_shared", "Candidate documents shared (to panellists)",
		"The recruitment team shares candidates' documents with Selection Committee panellists from the Documents page (one email per panellist).",
		"Panel Documents Shared", {"send_to_approvers": 1}, True, True, JOB_VARS + ", candidates, candidate_count, note, shared_by, documents_link"),
	("Interviews", "panel_job_files_shared", "Interview files shared (to panellists)",
		"The recruitment team shares job-level files (notification, panel details, assessment sheets, shortlisting note, HR notes, schedule) with panellists (workflow step 16).",
		"Panel Job Files Shared", {"send_to_approvers": 1}, True, True, JOB_VARS + ", files, note, shared_by, documents_link"),
	("Interviews", "hr_assessor_assigned", "HR assessor assigned (Round 1)",
		"Someone is made an HR assessor of a Round 1 / HR interaction interview (workflow step 13; one email per new assessor).",
		"HR Assessor Assignment", {"send_to_approvers": 1}, True, True,
		CANDIDATE_VARS + ", interview_date_time, meeting_platform, meeting_link, interview_location, assessment_link, updated"),
	("Interviews", "interview_invite_round1", "Interview invite: Round 1 / HR interaction", "Round 1 is scheduled (workflow step 13).",
		"Interview Invite (Round 1)", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", interview_date_time, meeting_link, meeting_platform, interview_location, rsvp_deadline, rsvp_link, rsvp_respond_link, updated, change_note"),
	("Interviews", "interview_call_letter", "Interview call letter: final interview", "The final interview is scheduled (workflow steps 14-16).",
		"Interview Call Letter", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", track, interview_date, interview_day, interview_time, interview_mode, meeting_platform, meeting_link, interview_location, meeting_details, login_time, rsvp_link, rsvp_respond_link, updated, change_note"),
	("Interviews", "interview_cancelled", "Interview cancelled (to candidate)",
		"An interview is cancelled and 'Email the candidate' is ticked.",
		"Interview Cancelled", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", interview_round, interview_date_time, reason"),
	("Interviews", "interview_reminder", "Interview reminder (to candidate)", "Daily, the day before a scheduled interview.",
		"Interview Reminder", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", interview_date_time, meeting_link"),
	("Selection & Offer", "reference_request", "Reference check request (to referee)",
		"The recruiter sends (or resends) a referee their reference check form link from the application's References panel (workflow step 21).",
		"Reference Check Request", {}, True, True, REFERENCE_VARS),
	("Selection & Offer", "reference_reminder", "Reference check reminder (to referee)",
		"Daily check: one reminder to a referee who has not answered a set number of days after the link was sent (Pathways Settings > Reference Checks).",
		"Reference Check Reminder", {}, True, True, REFERENCE_VARS),
	("Selection & Offer", "reference_received", "Reference received (to recruiter)",
		"A referee submits the reference check form. Goes to the staff member who sent the request.",
		"Reference Check Received", {"send_to_approvers": 1}, True, True, "candidate_name, application_id, job_title, referee_name, application_link, recipient_name"),
	("Selection & Offer", "offer_review_requested", "Appointment order ready for review",
		"A draft appointment order is submitted for review (workflow step 26). Goes to the Offer Reviewer Roles in Settings.",
		"Appointment Order Review Request", {"send_to_approvers": 1}, True, True, OFFER_VARS),
	("Selection & Offer", "offer_signature_requested", "Appointment order ready for signature",
		"A reviewed appointment order is approved for signature (workflow step 27). Goes to the Offer Signatory Roles in Settings.",
		"Appointment Order Signature Request", {"send_to_approvers": 1}, True, True, OFFER_VARS),
	("Selection & Offer", "offer_returned", "Appointment order returned for changes",
		"A reviewer or signatory returns an appointment order to draft. Goes to whoever submitted it for review.",
		"Appointment Order Returned", {"send_to_approvers": 1}, True, True, OFFER_VARS + ", remarks"),
	("Selection & Offer", "appointment_order", "Appointment order (to candidate)", "The signed appointment order is sent (workflow step 28). The letter PDF is attached.",
		"Appointment Order Covering Note", {"send_to_candidate": 1, "attach_record_files": 1}, True, True, CANDIDATE_VARS + ", acceptance_deadline, pnc_contacts, designation, portal_link"),
	("Selection & Offer", "regret_after_interview", "Regret after interview (to candidate)",
		"Sent from the consolidated score sheet to interviewed candidates marked Not selected (and, once the waitlist is released, waitlisted ones) who have not had it yet (workflow step 32).",
		"Regret After Interview", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS),
	("Onboarding & Closure", "panel_thanks", "Thank you to panellists",
		"Sent from the consolidated score sheet, once to each Selection Committee panellist; also starts their honorarium record (workflow step 33).",
		"Panel Thank You", {"send_to_approvers": 1}, True, True, "job_title, recipient_name, interview_date, is_external"),
	("Onboarding & Closure", "onboarding", "Onboarding documents (to new joiner)", "The candidate accepts the offer (workflow step 34).",
		"Onboarding Documents", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", joining_date, reporting_location, reporting_time, portal_link"),
	("Onboarding & Closure", "document_resubmission", "Joining document needs resubmission (to new joiner)",
		"Staff reviewing a new joiner's documents ask for one to be uploaded again (Documents > Onboarding Verification).",
		"Document Resubmission Request", {"send_to_candidate": 1}, True, True, CANDIDATE_VARS + ", document_name, rejection_reason, portal_link"),
	("Onboarding & Closure", "it_facilities", "Intimation to IT & Facilities", "Joining is confirmed, or a confirmed joining is rescheduled (laptop, NLS email ID).",
		"IT & Facilities Intimation", {"roles": ["Pathways IT Facilities"]}, True, True,
		"candidate_name, job_title, joining_date, candidate_email, candidate_mobile, department, reporting_location, request_link, updated"),
	("Onboarding & Closure", "it_facilities_completed", "IT & Facilities ready (to recruitment team)",
		"IT & Facilities complete a new joiner's request (laptop, NLS email ID, access card / seating). Also a bell notification to whoever confirmed the joining.",
		"IT & Facilities Completed", {"roles": ["Pathways Recruiter"]}, True, True,
		"candidate_name, job_title, joining_date, official_email, completed_by, joining_link, recipient_name"),
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
