# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Candidate portal accounts.

A candidate who applies without an account gets one: a Website User whose
username is their Candidate ID, with a temporary password emailed to them
("Candidate portal login" in Email Setup). They must set their own password
on first login (Candidate.password_change_required).

Candidates log in with their email address, their mobile number or their
Candidate ID. The mobile number is kept on the User (mobile_no) in one
standard form, and only when no other login uses it, so it always points at
exactly one account; before_login() brings what is typed into that form."""

import re

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


def enable_login_methods():
	"""Let candidates log in with their Candidate ID or mobile number as well
	as their email (Frappe always accepts the email)."""
	for setting in ("allow_login_using_user_name", "allow_login_using_mobile_number"):
		if not frappe.db.get_single_value("System Settings", setting):
			frappe.db.set_single_value("System Settings", setting, 1)


# Kept for callers of the old name.
enable_username_login = enable_login_methods


# ----------------------------------------------------------- mobile login

PHONE_LIKE = re.compile(r"^\+?[\d\s\-().]{7,20}$")


def normalize_mobile(value):
	"""One standard form for a mobile number: digits only, and for Indian
	numbers the 10-digit number without +91 / 91 / 0 in front.
	"+91 90000-18512", "091 9000018512" and "9000018512" all give
	"9000018512". Returns "" when it is not a phone number."""
	value = (value or "").strip()
	if not PHONE_LIKE.match(value):
		return ""
	digits = re.sub(r"\D", "", value)
	if len(digits) == 12 and digits.startswith("91"):
		digits = digits[2:]
	elif len(digits) == 11 and digits.startswith("0"):
		digits = digits[1:]
	return digits if 7 <= len(digits) <= 15 else ""


def mobile_owner(mobile, exclude_user=None):
	"""The login (User) already using this mobile number, if any."""
	filters = {"mobile_no": mobile}
	if exclude_user:
		filters["name"] = ["!=", exclude_user]
	return frappe.db.get_value("User", filters, "name")


def sync_login_mobile(user, mobile):
	"""Put the candidate's mobile number on their login so they can log in
	with it. Skipped when another login already uses the number: a number
	must lead to exactly one account. Returns True when it was set."""
	if not user or not frappe.db.exists("User", user):
		return False
	number = normalize_mobile(mobile)
	if not number:
		return False
	if mobile_owner(number, exclude_user=user):
		return False
	if frappe.db.get_value("User", user, "mobile_no") != number:
		frappe.db.set_value("User", user, "mobile_no", number, update_modified=False)
	return True


def before_login(login_manager=None):
	"""hooks.before_login: a mobile number may be typed with +91, spaces or
	dashes; match it to the stored form. Emails and Candidate IDs pass
	through unchanged (apart from stray spaces)."""
	typed = (frappe.form_dict.get("usr") or "").strip()
	if not typed:
		return
	number = normalize_mobile(typed)
	if number and number != typed and frappe.db.exists("User", {"mobile_no": number}):
		typed = number
	frappe.form_dict.usr = typed


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
	enable_login_methods()
	number = normalize_mobile(cand.mobile_number)
	if number and mobile_owner(number):
		number = ""  # someone else logs in with it; email and Candidate ID still work

	password = _temporary_password()
	first, _sep, last = (cand.full_name or cand.email).partition(" ")
	user = frappe.new_doc("User")
	user.update(
		{
			"email": cand.email,
			"first_name": first,
			"last_name": last or None,
			"username": cand.name,
			"mobile_no": number or None,
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
			"login_mobile": number,
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


# ----------------------------------------------------------- profile

PROFILE_EDITABLE = ("mobile_number", "date_of_birth", "gender", "address")


def _my_candidate():
	user = frappe.session.user
	name = frappe.db.get_value("Candidate", {"email": user}, "name") if user != "Guest" else None
	if not name or frappe.db.get_value("User", user, "user_type") == "System User":
		frappe.throw(_("Only candidates have a profile here."), frappe.PermissionError)
	return name


@frappe.whitelist()
def get_my_profile():
	"""Candidate portal > Profile: their own details."""
	name = _my_candidate()
	fields = ["name", "full_name", "email", "mobile_number", "date_of_birth", "gender", "address"]
	profile = frappe.db.get_value("Candidate", name, fields, as_dict=True)
	meta = frappe.get_meta("Candidate")
	profile["gender_options"] = [o for o in (meta.get_field("gender").options or "").split("\n") if o]
	profile["applications"] = frappe.db.count("Application", {"candidate": name})
	return profile


@frappe.whitelist(methods=["POST"])
def update_my_profile(data):
	"""Candidates may update their contact details; name and email are
	fixed (they identify the applications)."""
	name = _my_candidate()
	data = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	doc = frappe.get_doc("Candidate", name)
	for field in PROFILE_EDITABLE:
		if field in data:
			doc.set(field, (data.get(field) or None) if field != "address" else (data.get(field) or ""))
	if not (doc.mobile_number or "").strip():
		frappe.throw(_("Enter your mobile number."))
	number = normalize_mobile(doc.mobile_number)
	if not number:
		frappe.throw(_("Enter a valid mobile number."))
	if mobile_owner(number, exclude_user=frappe.session.user):
		frappe.throw(_("This mobile number is already used by another account. Enter a different number."))
	doc.save(ignore_permissions=True)  # Candidate.on_update puts it on the login
	return get_my_profile()
