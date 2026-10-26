# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Offers and appointment orders (workflow steps 22-29): default reviewer
and signatory roles in Pathways Settings and the starting set of
Appointment Order Templates.

Idempotent: roles are only filled when the table is empty and templates are
only created when missing, so staff edits made in Settings or Master Setup
are never overwritten. Also called from install.after_install."""

import frappe

DEFAULT_ROLES = (
	("offer_reviewer_roles", ("Pathways PNCO",)),
	("offer_signatory_roles", ("Pathways Registrar",)),
)

# Shared paragraphs. Placeholders are documented on the template's Letter
# Body field; the signature block is added under the letter automatically.
_ADDRESS = (
	"<p>To,<br><b>{{ candidate_name }}</b>"
	"{% if candidate_address %}<br>{{ candidate_address }}{% endif %}"
	"{% if candidate_email %}<br>Email: {{ candidate_email }}{% endif %}</p>"
)
_JOINING = (
	"<p>You are requested to report for duty on or before <b>{{ proposed_doj }}</b>"
	"{% if place_of_posting %} at {{ place_of_posting }}{% endif %}"
	"{% if reporting_to %}, where you will report to {{ reporting_to }}{% endif %}. "
	"Please carry the originals of your educational and experience certificates and a government-issued identity "
	"proof for verification at the time of joining.</p>"
)
_ACCEPT = (
	"<p>If you accept this appointment on the terms and conditions stated above, please sign a copy of this letter "
	"and send the signed copy, together with your confirmed date of joining, on or before "
	"<b>{{ acceptance_deadline }}</b>. You may also accept the offer and upload the signed copy from the NLSIU "
	"Careers portal. This offer lapses if it is not accepted by that date.</p>"
	"{% if terms %}<p><b>Other terms and conditions</b></p>{{ terms }}{% endif %}"
	"<p>We look forward to welcoming you to the National Law School of India University.</p>"
)
_GENERAL_TERMS = (
	"<li>Your appointment is subject to verification of your certificates, antecedents and references. If any "
	"information furnished by you is found to be false or suppressed, the appointment is liable to be terminated "
	"without notice.</li>"
	"<li>You will be governed by the rules, regulations, policies and code of conduct of the University in force "
	"from time to time, including the Policy on Prevention of Sexual Harassment.</li>"
	"<li>You shall not engage in any other employment, business or remunerated work without the prior written "
	"permission of the University.</li>"
)

TEMPLATES = [
	{
		"template_name": "Permanent Non-Teaching Appointment",
		"track": "Admin",
		"employment_type": "Permanent",
		"description": "Regular (permanent) administrative and non-teaching posts on a pay level, with probation.",
		"letter_body": (
			_ADDRESS
			+ "<p><b>Subject: Appointment to the post of {{ designation }}</b></p>"
			"<p>Dear {{ candidate_name }},</p>"
			"<p>With reference to your application ({{ application_id }}) and the subsequent interview, we are pleased to "
			"appoint you to the post of <b>{{ designation }}</b>{% if department %} in the {{ department }}{% endif %} "
			"of the National Law School of India University, Bengaluru, on the following terms and conditions:</p><ol>"
			"<li>The appointment is on a regular basis{% if pay_level %} in <b>{{ pay_level }}</b>{% endif %}"
			"{% if pay_scale %} (pay scale {{ pay_scale }}){% endif %}"
			"{% if gross_monthly_salary %}, with a gross monthly salary of <b>{{ gross_monthly_salary }}</b>{% endif %}.</li>"
			"{% if allowances %}<li>You will be eligible for the following allowances: {{ allowances }}.</li>{% endif %}"
			"<li>You will be on probation for a period of {{ probation_period or 'one year' }} from the date of joining, which "
			"may be extended at the discretion of the University. On satisfactory completion of probation you will be "
			"confirmed in the post.</li>"
			"<li>During probation the appointment may be terminated by either side with one month's notice or one month's "
			"salary in lieu of notice; after confirmation the notice period is three months.</li>"
			+ _GENERAL_TERMS
			+ "</ol>"
			+ _JOINING
			+ _ACCEPT
		),
	},
	{
		"template_name": "Consultant Engagement",
		"track": "",
		"employment_type": "Consultant",
		"description": "Consultants engaged on a consolidated monthly fee for a fixed term.",
		"letter_body": (
			_ADDRESS
			+ "<p><b>Subject: Engagement as {{ designation }} (Consultant)</b></p>"
			"<p>Dear {{ candidate_name }},</p>"
			"<p>With reference to your application ({{ application_id }}) and the subsequent interview, we are pleased to "
			"engage you as <b>{{ designation }}</b>{% if department %} with the {{ department }}{% endif %} of the "
			"National Law School of India University, Bengaluru, on a consultancy basis on the following terms:</p><ol>"
			"<li>The engagement is for a period of {{ contract_period or 'one year' }} from the date of joining"
			"{% if contract_end_date %}, ending on {{ contract_end_date }}{% endif %}, and may be renewed based on "
			"performance and the requirements of the University.</li>"
			"<li>You will be paid a consolidated fee of <b>{{ consolidated_fee }}</b> per month{% if allowances %}, "
			"together with {{ allowances }}{% endif %}, subject to deduction of tax at source as applicable. No other "
			"allowances or benefits are payable.</li>"
			"<li>This is a contractual engagement and does not confer any right to regular employment with the "
			"University.</li>"
			"<li>The engagement may be terminated by either side with one month's notice.</li>"
			+ _GENERAL_TERMS
			+ "</ol>"
			+ _JOINING
			+ _ACCEPT
		),
	},
	{
		"template_name": "Faculty Appointment (Assistant / Associate Professor)",
		"track": "Faculty",
		"employment_type": "Permanent",
		"designations": ["Assistant Professor", "Associate Professor"],
		"description": "Regular faculty appointments as Assistant or Associate Professor on the UGC pay level.",
		"letter_body": (
			_ADDRESS
			+ "<p><b>Subject: Appointment as {{ designation }}</b></p>"
			"<p>Dear {{ candidate_name }},</p>"
			"<p>On the recommendation of the Selection Committee, the University is pleased to appoint you as "
			"<b>{{ designation }}</b>{% if department %} in the {{ department }}{% endif %} at the National Law School "
			"of India University, Bengaluru, on the following terms and conditions:</p><ol>"
			"<li>The appointment is on a regular basis in the UGC pay matrix{% if pay_level %} at <b>{{ pay_level }}</b>{% endif %}"
			"{% if pay_scale %} ({{ pay_scale }}){% endif %}{% if gross_monthly_salary %}, with a gross monthly "
			"emolument of <b>{{ gross_monthly_salary }}</b>{% endif %}, together with allowances as admissible under the "
			"rules of the University{% if allowances %} ({{ allowances }}){% endif %}.</li>"
			"<li>You will be on probation for {{ probation_period or 'one year' }} from the date of joining.</li>"
			"<li>You will be required to teach courses assigned to you, undertake research and publication, supervise "
			"students and take on academic and administrative responsibilities as assigned by the Vice-Chancellor.</li>"
			"<li>Your service will be governed by the UGC Regulations and the statutes, regulations and service rules of "
			"the University as amended from time to time.</li>"
			+ _GENERAL_TERMS
			+ "</ol>"
			+ _JOINING
			+ _ACCEPT
		),
	},
	{
		"template_name": "Research / Project Appointment (Grant-funded)",
		"track": "Research",
		"employment_type": "Grant-funded",
		"designations": ["Research Associate", "Senior Research Associate", "Project Director"],
		"description": "Research and project staff paid from a grant; tenure is tied to the project.",
		"letter_body": (
			_ADDRESS
			+ "<p><b>Subject: Appointment as {{ designation }}</b></p>"
			"<p>Dear {{ candidate_name }},</p>"
			"<p>With reference to your application ({{ application_id }}) for the position of {{ job_title }} and the "
			"subsequent interview, we are pleased to appoint you as <b>{{ designation }}</b>"
			"{% if department %} with the {{ department }}{% endif %} at the National Law School of India University, "
			"Bengaluru, on the following terms and conditions:</p><ol>"
			"<li>The position is funded by a project grant. The appointment is for {{ contract_period or 'the duration of the project' }}"
			"{% if contract_end_date %}, up to {{ contract_end_date }}{% endif %}, and will end with the project or the "
			"grant, whichever is earlier.</li>"
			"<li>You will be paid a consolidated remuneration of <b>{{ consolidated_fee or gross_monthly_salary }}</b> per "
			"month{% if allowances %}, together with {{ allowances }}{% endif %}, subject to deduction of tax at source.</li>"
			"<li>You will work on the project deliverables assigned by the Project Director / Principal Investigator"
			"{% if reporting_to %} ({{ reporting_to }}){% endif %}.</li>"
			"<li>This appointment does not confer any right to regular employment with the University. It may be "
			"terminated by either side with one month's notice.</li>"
			+ _GENERAL_TERMS
			+ "</ol>"
			+ _JOINING
			+ _ACCEPT
		),
	},
	{
		"template_name": "Contract Appointment",
		"track": "",
		"employment_type": "Contract",
		"description": "Fixed-term contractual posts (teaching or non-teaching) on a consolidated salary.",
		"letter_body": (
			_ADDRESS
			+ "<p><b>Subject: Appointment as {{ designation }} on contract</b></p>"
			"<p>Dear {{ candidate_name }},</p>"
			"<p>With reference to your application ({{ application_id }}) and the subsequent interview, we are pleased to "
			"appoint you as <b>{{ designation }}</b>{% if department %} in the {{ department }}{% endif %} of the "
			"National Law School of India University, Bengaluru, on a contract basis on the following terms:</p><ol>"
			"<li>The appointment is for a fixed term of {{ contract_period or 'one year' }} from the date of joining"
			"{% if contract_end_date %}, ending on {{ contract_end_date }}{% endif %}. It may be renewed on satisfactory "
			"performance at the discretion of the University.</li>"
			"<li>You will be paid a consolidated salary of <b>{{ consolidated_fee or gross_monthly_salary }}</b> per month"
			"{% if pay_level %} (equivalent to {{ pay_level }}){% endif %}{% if allowances %}, together with {{ allowances }}{% endif %}.</li>"
			"<li>This contractual appointment does not confer any right to regular employment with the University. It may "
			"be terminated by either side with one month's notice or one month's salary in lieu of notice.</li>"
			+ _GENERAL_TERMS
			+ "</ol>"
			+ _JOINING
			+ _ACCEPT
		),
	},
]


def execute():
	seed_offer_settings()
	seed_appointment_order_templates()


def seed_offer_settings():
	settings = frappe.get_single("Pathways Settings")
	changed = False
	for fieldname, roles in DEFAULT_ROLES:
		if settings.get(fieldname):
			continue
		for role in roles:
			if frappe.db.exists("Role", role):
				settings.append(fieldname, {"role": role})
				changed = True
	if not settings.offer_signatory_title:
		settings.offer_signatory_title = "Registrar"
		changed = True
	if settings.offer_requires_green_sheet is None:
		settings.offer_requires_green_sheet = 1
		changed = True
	if changed:
		settings.flags.ignore_permissions = True
		settings.flags.ignore_mandatory = True
		settings.save()


def seed_appointment_order_templates():
	for template in TEMPLATES:
		if frappe.db.exists("Appointment Order Template", template["template_name"]):
			continue
		doc = frappe.new_doc("Appointment Order Template")
		doc.update({k: v for k, v in template.items() if k != "designations"})
		if doc.track and not frappe.db.exists("Recruitment Track", doc.track):
			doc.track = None
		for designation in template.get("designations") or []:
			if frappe.db.exists("Pathways Designation", designation):
				doc.append("designations", {"designation": designation})
		doc.is_active = 1
		doc.insert(ignore_permissions=True)
