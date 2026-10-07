# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Email Setup page: the outgoing mail server, and who receives each
recruitment email at each workflow stage (Recruitment Email Rule)."""

import email
from email.header import decode_header, make_header

import frappe
from frappe import _

ACCOUNT_NAME = "Pathways Outgoing"
SECURITY = ("STARTTLS", "SSL", "None")


def _require_manager():
	if not frappe.has_permission("Pathways Settings", "write"):
		frappe.throw(_("Only administrators can change email settings."), frappe.PermissionError)


def _account():
	name = frappe.db.get_value("Email Account", {"enable_outgoing": 1, "default_outgoing": 1}, "name") or (
		ACCOUNT_NAME if frappe.db.exists("Email Account", ACCOUNT_NAME) else None
	)
	return frappe.get_doc("Email Account", name) if name else None


def _account_summary(account):
	if not account:
		return None
	security = "SSL" if account.use_ssl_for_outgoing else "STARTTLS" if account.use_tls else "None"
	return {
		"name": account.name,
		"email_id": account.email_id,
		"sender_name": account.email_account_name,
		"smtp_server": account.smtp_server,
		"smtp_port": account.smtp_port,
		"security": security,
		"login_id": account.login_id if account.login_id_is_different else "",
		"has_password": bool(account.get_password(raise_exception=False)) if not account.awaiting_password else False,
		"enabled": bool(account.enable_outgoing),
	}


@frappe.whitelist()
def get_email_setup():
	from pathways.utils.communication import template_body

	_require_manager()
	rules = frappe.get_all(
		"Recruitment Email Rule",
		fields=["name", "label", "stage", "sort_order", "enabled", "is_automatic", "trigger_description", "send_to_candidate",
			"send_to_committee", "send_to_approvers", "extra_recipients", "cc", "email_template", "variables", "attach_record_files"],
		order_by="sort_order asc",
	)
	for rule in rules:
		rule["recipient_roles"] = frappe.get_all("Pathways Role", filters={"parent": rule.name, "parenttype": "Recruitment Email Rule"}, pluck="role")
		# Roles nobody (but Administrator, who is never emailed) holds.
		rule["empty_roles"] = [r for r in rule["recipient_roles"] if not _role_has_users(r)]
		rule["subject"], rule["response"] = _template_text(rule.email_template)
		rule["attachments"] = frappe.get_all(
			"File",
			filters={"attached_to_doctype": "Recruitment Email Rule", "attached_to_name": rule.name},
			fields=["name", "file_name", "file_url"],
			order_by="creation asc",
		)
	from pathways.permissions import get_pathways_roles

	# Every Email Template in the system, including ones added in Desk later.
	used_by = {}
	for rule in rules:
		used_by.setdefault(rule.email_template, []).append(rule.label)
	templates = [
		{"name": t.name, "subject": t.subject, "response": template_body(t), "used_by": used_by.get(t.name, [])}
		for t in frappe.get_all("Email Template", fields=["name", "subject", "response", "response_html", "use_html"], order_by="name asc")
	]

	return {
		"account": _account_summary(_account()),
		"reply_to": frappe.get_cached_doc("Pathways Settings").recruitment_contact_email or "",
		"rules": rules,
		"templates": templates,
		"role_options": sorted(get_pathways_roles()),
		"recent": _recent_emails(),
	}


@frappe.whitelist(methods=["POST"])
def save_email_account(data):
	"""Create or update the outgoing account. Frappe tests the SMTP login on
	save, so wrong details fail here with the server's message."""
	_require_manager()
	if isinstance(data, str):
		data = frappe.parse_json(data)
	security = data.get("security") if data.get("security") in SECURITY else "STARTTLS"

	account = _account() or frappe.new_doc("Email Account")
	if account.is_new():
		account.email_account_name = ACCOUNT_NAME
	account.update(
		{
			"email_id": (data.get("email_id") or "").strip(),
			"email_account_name": (data.get("sender_name") or "").strip() or account.email_account_name or ACCOUNT_NAME,
			"smtp_server": (data.get("smtp_server") or "").strip(),
			"smtp_port": frappe.utils.cint(data.get("smtp_port")) or (465 if security == "SSL" else 587),
			"use_tls": int(security == "STARTTLS"),
			"use_ssl_for_outgoing": int(security == "SSL"),
			"login_id_is_different": int(bool((data.get("login_id") or "").strip())),
			"login_id": (data.get("login_id") or "").strip() or None,
			"enable_outgoing": 1,
			"default_outgoing": 1,
			"enable_incoming": 0,
			"always_use_account_email_id_as_sender": 1,
			"always_use_account_name_as_sender_name": 1,
			"awaiting_password": 0,
		}
	)
	if data.get("password"):
		account.password = data["password"]
	if not account.smtp_server or not account.email_id:
		frappe.throw(_("Enter the sender email address and the SMTP server."))
	if account.is_new() and not data.get("password"):
		frappe.throw(_("Enter the password (or app password) for the mailbox."))
	account.save(ignore_permissions=True) if not account.is_new() else account.insert(ignore_permissions=True)
	return _account_summary(account)


@frappe.whitelist(methods=["POST"])
def send_test_email(recipient):
	"""Send right away (not queued) so the result is known on screen."""
	_require_manager()
	if not frappe.utils.validate_email_address(recipient):
		frappe.throw(_("Enter a valid email address."))
	if not _account():
		frappe.throw(_("Set up the outgoing mail server first."))
	frappe.sendmail(
		recipients=[recipient],
		subject=_("Pathways test email"),
		message=_("<p>This is a test email from Pathways. Outgoing email is working.</p>"),
		now=True,
	)
	return {"sent_to": recipient}


@frappe.whitelist(methods=["POST"])
def save_email_rule(event, data):
	_require_manager()
	if isinstance(data, str):
		data = frappe.parse_json(data)
	rule = frappe.get_doc("Recruitment Email Rule", event)
	rule.update(
		{
			"enabled": frappe.utils.cint(data.get("enabled")),
			"send_to_candidate": frappe.utils.cint(data.get("send_to_candidate")),
			"send_to_committee": frappe.utils.cint(data.get("send_to_committee")),
			"send_to_approvers": frappe.utils.cint(data.get("send_to_approvers")),
			"extra_recipients": data.get("extra_recipients") or "",
			"cc": data.get("cc") or "",
			"attach_record_files": frappe.utils.cint(data.get("attach_record_files")),
		}
	)
	# Switch to another template (any Email Template, incl. ones made in Desk).
	if data.get("email_template") and data["email_template"] != rule.email_template:
		if not frappe.db.exists("Email Template", data["email_template"]):
			frappe.throw(_("Email Template {0} does not exist.").format(data["email_template"]))
		rule.email_template = data["email_template"]
	if "recipient_roles" in data:
		rule.set("recipient_roles", [{"role": r} for r in data.get("recipient_roles") or [] if frappe.db.exists("Role", r)])
	rule.save(ignore_permissions=True)

	if "subject" in data or "response" in data:
		template = frappe.get_doc("Email Template", rule.email_template)
		if not (data.get("subject") or "").strip():
			frappe.throw(_("The subject cannot be empty."))
		template.subject = data.get("subject")
		template.response = data.get("response") or ""
		# Desk shows the HTML field when "Use HTML" is on: keep both in step.
		template.response_html = template.response
		template.use_html = 1
		template.save(ignore_permissions=True)
	return get_email_setup()


@frappe.whitelist(methods=["POST"])
def toggle_email_rule(event, enabled):
	_require_manager()
	frappe.db.set_value("Recruitment Email Rule", event, "enabled", frappe.utils.cint(enabled))
	return {"event": event, "enabled": frappe.utils.cint(enabled)}


def _subject(raw):
	try:
		return str(make_header(decode_header(email.message_from_string(raw or "")["Subject"] or "")))
	except Exception:
		return ""


def _recent_emails(limit=20):
	rows = frappe.get_all(
		"Email Queue",
		fields=["name", "status", "error", "creation", "reference_doctype", "reference_name", "message"],
		order_by="creation desc",
		limit_page_length=limit,
	)
	for row in rows:
		row["recipients"] = ", ".join(frappe.get_all("Email Queue Recipient", filters={"parent": row.name}, pluck="recipient"))
		row["subject"] = _subject(row.pop("message"))
		row["error"] = (row.error or "").strip().splitlines()[-1][:200] if row.error else ""
	return rows


@frappe.whitelist(methods=["POST"])
def remove_rule_attachment(event, file):
	"""Remove a file uploaded on an email rule."""
	_require_manager()
	if frappe.db.get_value("File", file, ["attached_to_doctype", "attached_to_name"]) != ("Recruitment Email Rule", event):
		frappe.throw(_("That file is not attached to this email."))
	frappe.delete_doc("File", file, ignore_permissions=True)
	return get_email_setup()


@frappe.whitelist(methods=["POST"])
def create_email_template(name, subject, response=""):
	"""A new Email Template from the Email Setup page (same as Desk)."""
	_require_manager()
	name = (name or "").strip()
	if not name or not (subject or "").strip():
		frappe.throw(_("Give the template a name and a subject."))
	if frappe.db.exists("Email Template", name):
		frappe.throw(_("An Email Template named {0} already exists.").format(name))
	frappe.get_doc({"doctype": "Email Template", "name": name, "subject": subject, "response": response, "use_html": 1}).insert(
		ignore_permissions=True
	)
	return get_email_setup()


def _sample_context():
	"""Placeholder values from a real recent job and application, so a
	preview reads like the email that would actually go out."""
	from pathways.utils.communication import candidate_email_context, job_email_context

	context = {"recipient_name": frappe.utils.get_fullname(frappe.session.user), "doc_name": "PWY-PREGS-2026-00001",
		"approver_label": "Registrar", "link": frappe.utils.get_url("/pathways/jobs"), "application_count": 0, "ratio": 5,
		"change": "deadline extended", "remarks": "", "interview_date_time": "12 Nov 2026, 10:30 AM",
		"meeting_link": "https://zoom.us/j/0000000000", "rsvp_deadline": "08 Nov 2026", "acceptance_deadline": "20 Nov 2026",
		"joining_date": "01 Dec 2026", "notification_number": "Notification No. 21/2026", "interview_date": "12 Nov 2026",
		"interview_day": "Thursday", "interview_time": "10:30 AM", "interview_mode": "Online", "meeting_platform": "Teams",
		"login_time": "10:10 AM", "pnc_contacts": "", "reporting_location": "", "reporting_time": ""}
	job = frappe.get_all("Job Opening", filters={"status": "Advertised"}, pluck="name", order_by="creation desc", limit=1)
	if job:
		context.update(job_email_context(frappe.get_doc("Job Opening", job[0])))
		context["application_count"] = frappe.db.count("Application", {"job_opening": job[0]})
	app = frappe.get_all("Application", pluck="name", order_by="creation desc", limit=1)
	if app:
		context.update(candidate_email_context(app[0])[0])
	return context


@frappe.whitelist()
def preview_email_rule(event):
	"""The email as it would be sent: rendered subject and message, the
	people it would go to, and its attachments."""
	_require_manager()
	from pathways.utils.communication import event_recipients, template_body

	rule = frappe.get_doc("Recruitment Email Rule", event)
	template = frappe.get_doc("Email Template", rule.email_template)
	context = _sample_context()
	try:
		subject = frappe.render_template(template.subject, context)
		message = frappe.render_template(template_body(template), context)
	except Exception as e:
		frappe.throw(_("The template has an error: {0}").format(str(e)))
	sample_job = frappe.get_all("Job Opening", filters={"status": "Advertised"}, pluck="name", order_by="creation desc", limit=1)
	recipients = event_recipients(rule, job_opening=sample_job[0] if sample_job else None)
	who = [
		label
		for label, on in (("The candidate", rule.send_to_candidate), ("The job's shortlisting committee", rule.send_to_committee),
			("The approvers of the current step", rule.send_to_approvers))
		if on
	]
	return {
		"label": rule.label,
		"subject": subject,
		"message": message,
		"template": rule.email_template,
		"recipient_groups": who + [r.role.replace("Pathways ", "") + " (role)" for r in rule.recipient_roles],
		"recipients": [{"email": e, "name": n} for e, n in recipients],
		"cc": rule.cc,
		"attachments": frappe.get_all("File", filters={"attached_to_doctype": "Recruitment Email Rule", "attached_to_name": rule.name}, pluck="file_name"),
		"attach_record_files": rule.attach_record_files,
		"enabled": rule.enabled,
	}


@frappe.whitelist(methods=["POST"])
def delete_email_rule(event):
	"""Remove an email: it is no longer sent. Its template is kept."""
	_require_manager()
	for file in frappe.get_all("File", filters={"attached_to_doctype": "Recruitment Email Rule", "attached_to_name": event}, pluck="name"):
		frappe.delete_doc("File", file, ignore_permissions=True)
	frappe.delete_doc("Recruitment Email Rule", event, ignore_permissions=True)
	return get_email_setup()


@frappe.whitelist(methods=["POST"])
def save_reply_to(email):
	"""Where replies to recruitment emails go (Pathways Settings >
	Recruitment Contact Email)."""
	_require_manager()
	email = (email or "").strip()
	if email and not frappe.utils.validate_email_address(email):
		frappe.throw(_("Enter a valid email address."))
	frappe.db.set_single_value("Pathways Settings", "recruitment_contact_email", email or None)
	frappe.clear_document_cache("Pathways Settings", "Pathways Settings")
	return email


def _role_has_users(role):
	return bool(
		frappe.get_all(
			"User",
			filters=[["Has Role", "role", "=", role], ["enabled", "=", 1], ["name", "not in", ("Administrator", "Guest")]],
			limit=1,
		)
	)


def _template_text(name):
	from pathways.utils.communication import template_body

	t = frappe.db.get_value("Email Template", name, ["subject", "response", "response_html", "use_html"], as_dict=True)
	return (t.subject, template_body(t)) if t else ("", "")
