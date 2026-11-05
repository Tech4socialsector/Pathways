# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""The candidate portal's notification bell.

Every email Pathways sends a candidate (pathways.utils.communication) also
leaves a notification in their portal: a Frappe Notification Log of type
Alert, which Frappe never emails, so nothing is sent twice. The bell reads
and marks only the signed-in candidate's own notifications."""

import frappe
from frappe import _
from frappe.utils import cint

from pathways.permissions import CANDIDATE_ROLE

TYPE = "Alert"
PORTAL = "/pathways/portal/applications"
MAX_PAGE = 50
# Login emails carry credentials and are about the portal itself.
SKIP_EVENTS = frozenset({"candidate_portal_access", "candidate_portal_existing_account"})


def _portal_user(email):
	"""The enabled candidate portal user for this address, or None."""
	user = frappe.db.get_value("User", {"name": email, "enabled": 1}, ["name", "user_type"], as_dict=True) if email else None
	if not user or user.user_type == "System User" or CANDIDATE_ROLE not in frappe.get_roles(user.name):
		return None
	return user.name


def _portal_link(reference_doctype, reference_name):
	"""The portal page a notification opens: the application it is about."""
	application = None
	if reference_doctype == "Application":
		application = reference_name
	elif reference_doctype and reference_name and frappe.get_meta(reference_doctype).has_field("application"):
		application = frappe.db.get_value(reference_doctype, reference_name, "application")
	if application and frappe.db.exists("Application", application):
		suffix = f"?interview={reference_name}" if reference_doctype == "Interview" else ""
		return f"{PORTAL}/{application}{suffix}"
	return PORTAL


def notify_candidate(event, email, subject, reference_doctype=None, reference_name=None):
	"""Record a portal notification for the email just sent to a candidate.
	Never breaks the send."""
	if event in SKIP_EVENTS:
		return
	try:
		user = _portal_user(email)
		if not user:
			return
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"type": TYPE,
				"for_user": user,
				"subject": frappe.utils.strip_html(subject or "")[:300],
				"document_type": reference_doctype,
				"document_name": reference_name,
				"link": _portal_link(reference_doctype, reference_name),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(title=f"Pathways candidate notification failed: {event} to {email}")


def _me():
	user = frappe.session.user
	if user == "Guest" or not _portal_user(user):
		frappe.throw(_("Only candidates have portal notifications."), frappe.PermissionError)
	return user


@frappe.whitelist()
def get_my_notifications(limit=20):
	"""The bell: newest first, and how many are unread."""
	user = _me()
	limit = min(max(cint(limit) or 20, 1), MAX_PAGE)
	filters = {"for_user": user, "type": TYPE}
	rows = frappe.get_all(
		"Notification Log",
		filters=filters,
		fields=["name", "subject", "link", "read", "creation", "document_type"],
		order_by="creation desc",
		limit_page_length=limit,
	)
	for row in rows:
		row.subject = frappe.utils.strip_html(row.subject or "")
		# Only links inside the portal are followed.
		row.link = row.link if (row.link or "").startswith(PORTAL) else PORTAL
		row.read = cint(row.read)
	return {"notifications": rows, "unread": frappe.db.count("Notification Log", {**filters, "read": 0})}


@frappe.whitelist(methods=["POST"])
def mark_my_notifications_read(names=None):
	"""Mark the given notifications (a JSON list), or all of them, as read.
	Only the candidate's own are touched; others are ignored."""
	user = _me()
	if isinstance(names, str):
		names = frappe.parse_json(names) if names.strip().startswith("[") else [names]
	filters = {"for_user": user, "type": TYPE, "read": 0}
	if names is not None:
		names = [n for n in names if isinstance(n, str)][:MAX_PAGE]
		if not names:
			return {"unread": frappe.db.count("Notification Log", filters)}
		filters["name"] = ["in", names]
	for name in frappe.get_all("Notification Log", filters=filters, pluck="name"):
		frappe.db.set_value("Notification Log", name, "read", 1, update_modified=False)
	return {"unread": frappe.db.count("Notification Log", {"for_user": user, "type": TYPE, "read": 0})}
