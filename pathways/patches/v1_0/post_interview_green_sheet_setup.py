# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Selection (Post-Interview) Green Sheet setup.

1. Every Recruitment Track gets a track-wide Approval Chain Template for the
   Post-Interview Green Sheet, so a sheet can always be submitted: Recruiter
   -> PNCO -> CFO -> Registrar -> VC (workflow step 25). The Permanent and
   Consultant sheets in the workflow folder carry the same signatories, so
   one track-wide chain serves both; a per-employment-type chain can be added
   in Master Setup > Approval Chains and wins over it. Tracks that already
   have a track-wide chain (e.g. the seeded Admin and Research ones) are left
   alone, as are templates staff have edited.
2. The approval email now goes out for every approvable document, so its
   template no longer says "Pre-Recruitment" — updated only when staff have
   not edited it.

Idempotent: safe to run again.
"""

import frappe

APPLIES_TO = "Post-Interview Green Sheet"
DEFAULT_STEPS = (
	("Pathways Recruiter", "Recruiter"),
	("Pathways PNCO", "PNCO"),
	("Pathways CFO", "Chief Finance Officer"),
	("Pathways Registrar", "Registrar"),
	("Pathways Vice Chancellor", "Vice Chancellor"),
)

OLD_APPROVAL_LINE = (
	"<p>The Pre-Recruitment Green Sheet <b>{{ doc_name }}</b> for <b>{{ job_title }}</b> is awaiting your approval "
)
NEW_APPROVAL_LINE = (
	"<p>The {{ doc_type or 'Pre-Recruitment Green Sheet' }} <b>{{ doc_name }}</b> for <b>{{ job_title }}</b> is awaiting your approval "
)


def execute():
	seed_post_interview_chains()
	update_approval_email()


def seed_post_interview_chains(employment_type=None):
	"""One template per track (and employment type, when given) where none
	exists. Returns the names created."""
	created = []
	steps = [(role, label) for role, label in DEFAULT_STEPS if frappe.db.exists("Role", role)]
	if not steps:
		return created
	for track in frappe.get_all("Recruitment Track", filters={"is_active": 1}, pluck="name"):
		existing = frappe.get_all(
			"Approval Chain Template", filters={"track": track, "applies_to": APPLIES_TO}, pluck="employment_type"
		)
		if any((t or None) == (employment_type or None) for t in existing):
			continue
		name = f"{track} - {APPLIES_TO}" + (f" ({employment_type})" if employment_type else "")
		if frappe.db.exists("Approval Chain Template", name):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Approval Chain Template",
				"template_name": name,
				"track": track,
				"applies_to": APPLIES_TO,
				"employment_type": employment_type,
				"is_active": 1,
				"steps": [
					{"sequence": seq, "approver_type": "Role", "approver_role": role, "approver_label": label}
					for seq, (role, label) in enumerate(steps, start=1)
				],
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(doc.name)
	return created


def update_approval_email():
	name = "Green Sheet Approval Request"
	response = frappe.db.get_value("Email Template", name, "response")
	if response and OLD_APPROVAL_LINE in response:
		frappe.db.set_value("Email Template", name, "response", response.replace(OLD_APPROVAL_LINE, NEW_APPROVAL_LINE))
