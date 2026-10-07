import frappe

from pathways.master_data import seed_master_data
from pathways.permissions import CANDIDATE_ROLE, DEFAULT_PATHWAYS_ROLES

DEFAULT_DECLARATION = (
	"I hereby certify that the information furnished in this application is true, complete, and correct. "
	"I further certify that no adverse findings have been recorded against me in any disciplinary "
	"proceedings, and that no complaint of sexual harassment is pending before any authority or forum. "
	"I have not been dismissed from service, debarred from future employment, or convicted of any offence, "
	"and no criminal case is presently pending against me. I understand that, in the event any information "
	"is found to be false, misleading, suppressed, or concealed at any stage, my candidature is liable to be "
	"cancelled and, if appointed, my employment may be terminated with immediate effect, without any prior "
	"notice or opportunity of being heard, and without payment of any compensation or notice pay. I also "
	"understand that my candidature may not be considered if I am absent on the scheduled date of interview, "
	"and that the decisions of the Selection Committee and the University's bodies shall be final and binding."
)

# Starting point matching the NLSIU application forms; maintained afterwards
# from Master Setup. Only created when missing.
DEFAULT_APPLICATION_DOCUMENT_TYPES = [
	("Identity Proof (Aadhaar / PAN / Passport / DL / Voter ID)", "Mandatory"),
	("Experience Certificate #1", "Mandatory"),
	("Experience Certificate #2", "Optional"),
	("Latest Pay Slip", "Mandatory"),
]

DEFAULT_CANDIDATE_SOURCES = [
	"Social Media (LinkedIn)",
	"Social Media (Facebook)",
	"Social Media (Twitter)",
	"Social Media (Instagram)",
	"NLSIU Website",
	"Other Website",
	"Staff of NLSIU",
	"Students of NLSIU",
	"Staff of NLUs/Other Universities",
	"Students of NLUs/Other Universities",
]

# Recruitment emails live in pathways.utils.email_events (one template per
# workflow email, worded as in the workflow folder). Only templates no
# Email Setup rule owns stay here.
EMAIL_TEMPLATES = [
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
]


def after_install():
	create_roles()
	create_email_templates()
	seed_settings()
	from pathways.utils.email_events import ensure_email_events

	ensure_email_events()
	seed_application_masters()
	seed_master_data()


def create_roles():
	for role_name in DEFAULT_PATHWAYS_ROLES:
		if frappe.db.exists("Role", role_name):
			# A candidate role with desk access turns candidates into staff users.
			if role_name == CANDIDATE_ROLE:
				frappe.db.set_value("Role", role_name, "desk_access", 0)
			continue
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = 0 if role_name == CANDIDATE_ROLE else 1
		role.insert(ignore_permissions=True)
	frappe.db.commit()


def seed_settings():
	"""Defaults for Pathways Settings fields that are not plain field
	defaults (child table, long text) plus the behaviour switches, so an
	upgraded site keeps today's behaviour."""
	settings = frappe.get_single("Pathways Settings")
	if not settings.get("pathways_roles"):
		for role in DEFAULT_PATHWAYS_ROLES:
			if frappe.db.exists("Role", role):
				settings.append("pathways_roles", {"role": role})
	for fieldname, roles in (
		("document_verifier_roles", ("Pathways Admin", "Pathways PNCO")),
		("corrigendum_signer_roles", ("Pathways Admin", "Pathways Registrar")),
	):
		if not settings.get(fieldname):
			for role in roles:
				if frappe.db.exists("Role", role):
					settings.append(fieldname, {"role": role})
	if not settings.application_declaration:
		settings.application_declaration = DEFAULT_DECLARATION
	if not settings.approval_override_role and frappe.db.exists("Role", "Pathways Admin"):
		settings.approval_override_role = "Pathways Admin"
	if not settings.status_override_role:
		settings.status_override_role = "System Manager"
	if not settings.application_max_file_size_mb:
		settings.application_max_file_size_mb = 5
	if not settings.application_allowed_formats:
		settings.application_allowed_formats = "PDF, JPG, JPEG, PNG"
	settings.flags.ignore_permissions = True
	settings.flags.ignore_mandatory = True
	settings.save()


def seed_application_masters():
	for name, requirement in DEFAULT_APPLICATION_DOCUMENT_TYPES:
		if frappe.db.exists("Document Type Master", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Document Type Master",
				"document_name": name,
				"used_in": "Application",
				"requirement": requirement,
				"max_file_size_mb": 2,
				"allowed_formats": "PDF, JPG, JPEG, PNG",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
	for source in DEFAULT_CANDIDATE_SOURCES:
		if not frappe.db.exists("Candidate Source", source):
			frappe.get_doc({"doctype": "Candidate Source", "source_name": source, "is_active": 1}).insert(
				ignore_permissions=True
			)


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


