# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.utils import now_datetime


def template_body(template):
	"""An Email Template's message: its HTML when "Use HTML" is ticked (as
	templates edited in Desk store it), otherwise the rich-text response."""
	if template.get("use_html") and (template.get("response_html") or "").strip():
		return template.response_html
	return template.response or ""


def send_templated_email(email_template, recipient, reference_doctype, reference_name, args=None):
	"""Send an email via a Frappe Email Template (Jinja-rendered) and log it
	to Communication Log, per the notification matrix in the architecture
	blueprint. Never call frappe.sendmail directly from business logic —
	always route through here so every recruitment email is auditable.
	"""
	status = "Sent"
	try:
		template = frappe.get_doc("Email Template", email_template)
		context = args or {}
		subject = frappe.render_template(template.subject, context)
		message = frappe.render_template(template_body(template), context)
		frappe.sendmail(recipients=[recipient], subject=subject, message=message)
	except Exception:
		status = "Failed"
		frappe.log_error(
			title=f"Pathways email send failed: {email_template} to {recipient}",
			reference_doctype=reference_doctype,
			reference_name=reference_name,
		)

	log = frappe.new_doc("Communication Log")
	log.reference_doctype = reference_doctype
	log.reference_name = reference_name
	log.email_template = email_template
	log.recipient = recipient
	log.sent_on = now_datetime()
	log.status = status
	log.insert(ignore_permissions=True)
	frappe.db.commit()
	return status


# ------------------------------------------------------------ event emails
# Who gets each recruitment email is configured per event on the Email Setup
# page (Recruitment Email Rule). Business code only says what happened.


def send_event(event, reference_doctype, reference_name, context=None, candidate=None, job_opening=None, approvers=None, cc=None):
	"""Queue the emails for `event` after the current transaction commits, so
	a failed or rolled-back action sends nothing and sending never slows or
	breaks the action itself.

	candidate: {"email", "name"} when the rule may go to the candidate;
	job_opening: for "the job's committee"; approvers: user IDs for "the
	approvers of the current step"; cc: extra addresses copied on this
	send, on top of the rule's own CC."""
	if not frappe.db.exists("Recruitment Email Rule", {"name": event, "enabled": 1}):
		return
	frappe.enqueue(
		"pathways.utils.communication._send_event",
		enqueue_after_commit=True,
		# Not "event": frappe.enqueue has its own parameter by that name and
		# would swallow it, so the job would run without knowing which email.
		rule_event=event,
		reference_doctype=reference_doctype,
		reference_name=reference_name,
		context=context or {},
		candidate=candidate,
		job_opening=job_opening,
		approvers=approvers,
		extra_cc=parse_emails(cc),
	)


def parse_emails(value):
	"""Valid, de-duplicated addresses from a list or a comma/semicolon string."""
	if not value:
		return []
	if isinstance(value, str):
		value = frappe.parse_json(value) if value.strip().startswith("[") else re.split(r"[,;\s]+", value)
	out = []
	for email in value:
		email = (email or "").strip()
		if not email:
			continue
		if not frappe.utils.validate_email_address(email):
			frappe.throw(frappe._("{0} is not a valid email address.").format(email))
		if email.lower() not in [e.lower() for e in out]:
			out.append(email)
	return out


def event_recipients(rule, candidate=None, job_opening=None, approvers=None):
	"""[(email, name)] for a rule, without duplicates."""
	people = []
	if rule.send_to_candidate and candidate and candidate.get("email"):
		people.append((candidate["email"], candidate.get("name") or ""))

	users = list(approvers or []) if rule.send_to_approvers else []
	if rule.send_to_committee and job_opening:
		committee = frappe.db.get_value("Shortlisting Committee", {"job_opening": job_opening}, "name")
		if committee:
			users += frappe.get_all("Committee Member Row", filters={"parent": committee, "parenttype": "Shortlisting Committee"}, pluck="member")
	roles = [row.role for row in rule.recipient_roles or [] if row.role]
	if roles:
		users += frappe.get_all("Has Role", filters={"role": ["in", roles], "parenttype": "User"}, pluck="parent")
	for user in dict.fromkeys(users):
		if user in ("Administrator", "Guest"):
			continue
		row = frappe.db.get_value("User", user, ["email", "full_name", "enabled"], as_dict=True)
		if row and row.enabled and row.email:
			people.append((row.email, row.full_name or ""))

	for email in (rule.extra_recipients or "").split(","):
		if email.strip():
			people.append((email.strip(), ""))

	seen, out = set(), []
	for email, name in people:
		if email.lower() not in seen:
			seen.add(email.lower())
			out.append((email, name))
	return out


def event_attachments(rule, reference_doctype=None, reference_name=None):
	"""File names to attach: files uploaded on the rule (Email Setup), plus
	the record's own files when the rule asks for them."""
	files = frappe.get_all("File", filters={"attached_to_doctype": "Recruitment Email Rule", "attached_to_name": rule.name}, pluck="name")
	if rule.attach_record_files and reference_doctype and reference_name:
		files += frappe.get_all("File", filters={"attached_to_doctype": reference_doctype, "attached_to_name": reference_name}, pluck="name")
	return list(dict.fromkeys(files))


def _send_event(rule_event=None, reference_doctype=None, reference_name=None, context=None, candidate=None, job_opening=None, approvers=None, extra_cc=None, event=None):
	event = rule_event or event
	context = context or {}
	rule = frappe.get_doc("Recruitment Email Rule", event)
	template = frappe.get_doc("Email Template", rule.email_template)
	cc = [e.strip() for e in (rule.cc or "").split(",") if e.strip()]
	cc += [e for e in extra_cc or [] if e.lower() not in {c.lower() for c in cc}]
	attachments = [{"fid": f} for f in event_attachments(rule, reference_doctype, reference_name)]
	# Replies go to the recruitment team (Email Setup > Reply-to address).
	reply_to = frappe.get_cached_doc("Pathways Settings").recruitment_contact_email or None
	recipients = event_recipients(rule, candidate, job_opening, approvers)
	if not recipients:
		# Nobody to send to (e.g. no user holds the rule's roles): leave a
		# trace in the Error Log instead of failing silently.
		frappe.log_error(
			title=f"Pathways email not sent: no recipients for {rule.label}",
			message=f"Event {event} for {reference_doctype} {reference_name}. Check the recipients in Email Setup.",
			reference_doctype=reference_doctype,
			reference_name=reference_name,
		)
	for email, name in recipients:
		status = "Sent"
		try:
			values = {"contact_email": reply_to or "", **context, "recipient_name": name or (context.get("candidate_name") if candidate and email == candidate.get("email") else "") or "Colleague"}
			frappe.sendmail(
				recipients=[email],
				cc=cc,
				subject=frappe.render_template(template.subject, values),
				message=frappe.render_template(template_body(template), values),
				reference_doctype=reference_doctype,
				reference_name=reference_name,
				attachments=attachments or None,
				reply_to=reply_to,
			)
		except Exception:
			status = "Failed"
			frappe.log_error(title=f"Pathways email failed: {event} to {email}", reference_doctype=reference_doctype, reference_name=reference_name)
		log = frappe.new_doc("Communication Log")
		log.update(
			{
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"email_template": rule.email_template,
				"recipient": email,
				"sent_on": now_datetime(),
				"status": status,
			}
		)
		log.insert(ignore_permissions=True)
	frappe.db.commit()


def job_email_context(job):
	"""Placeholders every job-level email can use."""
	from pathways.pathways.doctype.job_opening.job_opening import get_advertisement_url

	return {
		"job_title": job.job_title,
		"job_code": job.position or job.name,
		"department": job.department,
		"vacancies": job.vacancies,
		"deadline": frappe.utils.format_datetime(job.application_deadline, "dd MMM yyyy, h:mm a") if job.application_deadline else "",
		"posting_link": get_advertisement_url(job.name),
		"job_link": frappe.utils.get_url(f"/pathways/jobs/{job.name}"),
	}


def candidate_email_context(application):
	"""Placeholders and recipient for candidate emails about an application."""
	app = frappe.get_doc("Application", application) if isinstance(application, str) else application
	person = frappe.db.get_value("Candidate", app.candidate, ["full_name", "email", "mobile_number"], as_dict=True) or {}
	context = {
		"candidate_name": person.get("full_name"),
		"candidate_email": person.get("email"),
		"candidate_mobile": person.get("mobile_number"),
		"application_id": app.application_id,
		"job_title": frappe.db.get_value("Job Opening", app.job_opening, "job_title"),
		"track": frappe.db.get_value("Job Opening", app.job_opening, "track"),
		"contact_email": frappe.get_cached_doc("Pathways Settings").recruitment_contact_email or "",
	}
	return context, {"email": person.get("email"), "name": person.get("full_name")}
