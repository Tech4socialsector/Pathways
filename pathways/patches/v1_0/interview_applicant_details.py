import frappe


def execute():
	"""Fill Applicant Name, Job Opening and Position on existing interviews."""
	for name in frappe.get_all("Interview", pluck="name"):
		doc = frappe.get_doc("Interview", name)
		doc.set_applicant_details()
		doc.db_set({"candidate": doc.candidate, "candidate_name": doc.candidate_name, "job_title": doc.job_title, "position": doc.position}, update_modified=False)
