import frappe


def execute():
	"""Candidates with a portal login own their Candidate record and applications."""
	from pathways.utils.candidate_account import claim_records

	for cand in frappe.get_all("Candidate", fields=["name", "email"]):
		claim_records(cand.name, cand.email)
