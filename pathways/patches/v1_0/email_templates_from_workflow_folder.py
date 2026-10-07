import frappe


def execute():
	"""Reword the recruitment emails as in the workflow folder (Email to
	Shortlisting Committee, Round 1 invite, Interview Call Letter, Regret
	Mail, Appointment letter, Onboarding, IT-Facilities). Templates staff
	have edited since they were created are left alone."""
	from pathways.utils.email_events import TEMPLATES, ensure_email_events

	for name, (subject, response) in TEMPLATES.items():
		row = frappe.db.get_value("Email Template", name, ["creation", "modified"], as_dict=True)
		if row and (row.modified - row.creation).total_seconds() > 5:
			continue
		if row:
			frappe.db.set_value(
				"Email Template",
				name,
				{"subject": subject, "response": response, "response_html": response, "use_html": 1},
				update_modified=False,
			)
	# Duplicates no rule uses (the rules send "Onboarding Documents" and
	# "Panel Thank You").
	used = set(frappe.get_all("Recruitment Email Rule", pluck="email_template"))
	for name in ("Onboarding Email", "Panelist Thanks"):
		if frappe.db.exists("Email Template", name) and name not in used:
			frappe.delete_doc("Email Template", name, ignore_permissions=True, force=True)
	ensure_email_events()
