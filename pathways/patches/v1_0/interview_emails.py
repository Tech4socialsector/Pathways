import frappe


def execute():
	"""Interview stage emails: panellist invitation, and the RSVP link in the
	Round 1 invite and call letter (templates staff have not edited)."""
	from pathways.utils.email_events import TEMPLATES, ensure_email_events

	for name in ("Interview Invite (Round 1)", "Interview Call Letter"):
		row = frappe.db.get_value("Email Template", name, ["creation", "modified"], as_dict=True)
		if row and (row.modified - row.creation).total_seconds() <= 5:
			subject, response = TEMPLATES[name]
			frappe.db.set_value("Email Template", name, {"subject": subject, "response": response, "response_html": response}, update_modified=False)
	ensure_email_events()
