# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Candidate portal accounts.

A candidate who applies without an account gets one: a Website User whose
username is their Candidate ID, with a temporary password emailed to them
("Candidate portal login" in Email Setup). They must set their own password
on first login (Candidate.password_change_required)."""

import secrets
import string

import frappe
from frappe import _

from pathways.permissions import CANDIDATE_ROLE

PORTAL_PATH = "/pathways/portal/applications"


def _temporary_password(length=12):
	# Letters and digits only, with at least one of each kind, so it is easy
	# to type and passes Frappe's password policy if one is set.
	alphabet = string.ascii_letters + string.digits
	while True:
		pwd = "".join(secrets.choice(alphabet) for _ in range(length))
		if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and any(c.isdigit() for c in pwd):
			return pwd


def enable_username_login():
	if not frappe.db.get_single_value("System Settings", "allow_login_using_user_name"):
		frappe.db.set_single_value("System Settings", "allow_login_using_user_name", 1)


def claim_records(candidate, email=None):
	"""Make the candidate's login the owner of their Candidate record and
	applications. Candidates read only what they own (role permission "only
	if creator"), and a guest's application is owned by Guest."""
	email = email or frappe.db.get_value("Candidate", candidate, "email")
	if not email or not frappe.db.exists("User", email):
		return
	frappe.db.sql("update `tabCandidate` set owner=%s where name=%s and owner!=%s", (email, candidate, email))
	frappe.db.sql("update `tabApplication` set owner=%s where candidate=%s and owner!=%s", (email, candidate, email))


def create_portal_account(candidate):
	"""Background job after an application: create the candidate's login if
	they have none and email the credentials. Does nothing when a user with
	their email already exists (they already have a login)."""
	cand = frappe.get_doc("Candidate", candidate)
	if not cand.email or frappe.db.exists("User", cand.email):
		return False
	enable_username_login()

	password = _temporary_password()
	first, _sep, last = (cand.full_name or cand.email).partition(" ")
	user = frappe.new_doc("User")
	user.update(
		{
			"email": cand.email,
			"first_name": first,
			"last_name": last or None,
			"username": cand.name,
			"user_type": "Website User",
			"send_welcome_email": 0,
			"new_password": password,
		}
	)
	user.flags.ignore_password_policy = True
	user.append("roles", {"role": CANDIDATE_ROLE})
	user.insert(ignore_permissions=True)
	cand.db_set("password_change_required", 1, update_modified=False)
	claim_records(cand.name, cand.email)
	frappe.db.commit()

	from pathways.utils.communication import _send_event

	# Sent here, not queued: the password must not sit in the job queue.
	_send_event(
		rule_event="candidate_portal_access",
		reference_doctype="Candidate",
		reference_name=cand.name,
		context={
			"candidate_name": cand.full_name,
			"candidate_id": cand.name,
			"username": cand.name,
			"temporary_password": password,
			"login_link": frappe.utils.get_url(f"/login?redirect-to={PORTAL_PATH}"),
		},
		candidate={"email": cand.email, "name": cand.full_name},
	)
	return True


def queue_portal_account(candidate):
	if not frappe.db.get_value("Recruitment Email Rule", "candidate_portal_access", "enabled"):
		return
	frappe.enqueue(
		"pathways.utils.candidate_account.create_portal_account",
		candidate=candidate,
		enqueue_after_commit=True,
	)


def must_change_password(user=None):
	user = user or frappe.session.user
	return bool(frappe.db.get_value("Candidate", {"email": user}, "password_change_required"))


@frappe.whitelist(methods=["POST"])
def change_password(current_password, new_password):
	"""Candidate portal: replace the temporary password with their own."""
	from frappe.utils.password import check_password, update_password

	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please log in first."), frappe.PermissionError)
	new_password = new_password or ""
	if len(new_password) < 8:
		frappe.throw(_("The new password must be at least 8 characters."))
	if new_password == current_password:
		frappe.throw(_("Choose a password different from the temporary one."))
	try:
		check_password(user, current_password)
	except frappe.AuthenticationError:
		frappe.clear_last_message()
		frappe.throw(_("The current password is not correct."))

	from frappe.core.doctype.user.user import test_password_strength, handle_password_test_fail

	result = test_password_strength(new_password, user_data=(frappe.db.get_value("User", user, "first_name"), user))
	feedback = (result or {}).get("feedback") or {}
	if feedback and not feedback.get("password_policy_validation_passed", True):
		handle_password_test_fail(feedback)

	update_password(user, new_password)
	frappe.db.set_value("Candidate", {"email": user}, "password_change_required", 0, update_modified=False)
	return True
