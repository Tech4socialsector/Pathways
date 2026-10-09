import frappe


def execute():
	"""Candidates log in with email, mobile number or Candidate ID: turn on
	mobile login, put each candidate's mobile number on their login (unless
	another login already uses it) and refresh the login email if staff have
	not edited it."""
	from pathways.utils.candidate_account import enable_login_methods, normalize_mobile, sync_login_mobile
	from pathways.utils.email_events import TEMPLATES

	enable_login_methods()

	seen = set()
	for c in frappe.get_all("Candidate", fields=["email", "mobile_number"], order_by="creation asc"):
		number = normalize_mobile(c.mobile_number)
		# Two candidates with one number: the first keeps it, so a number
		# never leads to two accounts. The others still log in by email.
		if not number or number in seen or not frappe.db.exists("User", c.email):
			continue
		if sync_login_mobile(c.email, c.mobile_number):
			seen.add(number)

	name = "Candidate Portal Login"
	row = frappe.db.get_value("Email Template", name, ["creation", "modified"], as_dict=True)
	if row and (row.modified - row.creation).total_seconds() <= 5:
		subject, response = TEMPLATES[name]
		frappe.db.set_value("Email Template", name, {"subject": subject, "response": response, "response_html": response}, update_modified=False)
