import frappe


def execute():
	"""Candidates log in with their Candidate ID as username."""
	from pathways.utils.candidate_account import enable_username_login
	from pathways.utils.email_events import ensure_email_events

	enable_username_login()
	ensure_email_events()
