# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Communications page and the "Emails" panel on an application.

Every recruitment email is logged in Communication Log (one row per
recipient, see pathways.utils.communication). A log row only says which
template went to whom about which record, so this module adds what staff
ask about: the email event (from the Email Setup rules using the template),
the job and application the record belongs to, and the email as it was sent
(from Frappe's Email Queue, while it is kept there).

Read access is plain Role Permissions on Communication Log."""

import email
from email.header import decode_header, make_header

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, get_datetime, getdate

PAGE_LENGTH = 50


def _require_read():
	if not frappe.has_permission("Communication Log", "read"):
		frappe.throw(_("You cannot view the communication log."), frappe.PermissionError)


def _events_by_template():
	out = {}
	for rule in frappe.get_all("Recruitment Email Rule", fields=["name", "label", "email_template"]):
		out.setdefault(rule.email_template, []).append({"event": rule.name, "label": rule.label})
	return out


def _logged_doctypes():
	return [d for d in frappe.db.sql_list("select distinct reference_doctype from `tabCommunication Log`") if d]


def _has(doctype, field):
	try:
		return frappe.get_meta(doctype).has_field(field)
	except frappe.DoesNotExistError:
		return False


def _reference_condition(job_opening=None, application=None):
	"""SQL (and values) matching log rows whose record belongs to the job or
	application: the record itself, or any record with a job_opening /
	application field pointing at it."""
	parts, values = [], {}
	if application:
		parts.append("(log.reference_doctype = 'Application' and log.reference_name = %(application)s)")
		values["application"] = application
	if job_opening:
		parts.append("(log.reference_doctype = 'Job Opening' and log.reference_name = %(job_opening)s)")
		values["job_opening"] = job_opening
	for i, doctype in enumerate(_logged_doctypes()):
		if doctype in ("Application", "Job Opening"):
			continue
		table = f"`tab{doctype}`"
		if application and _has(doctype, "application"):
			parts.append(
				f"(log.reference_doctype = %(dt{i})s and log.reference_name in (select name from {table} where application = %(application)s))"
			)
			values[f"dt{i}"] = doctype
		if job_opening and _has(doctype, "job_opening"):
			parts.append(
				f"(log.reference_doctype = %(dt{i})s and log.reference_name in (select name from {table} where job_opening = %(job_opening)s))"
			)
			values[f"dt{i}"] = doctype
	if job_opening and not application:
		# Records hanging off the job's applications (interviews, offers...).
		for i, doctype in enumerate(_logged_doctypes()):
			if doctype in ("Application", "Job Opening") or _has(doctype, "job_opening") or not _has(doctype, "application"):
				continue
			parts.append(
				f"(log.reference_doctype = %(adt{i})s and log.reference_name in (select r.name from `tab{doctype}` r "
				f"join `tabApplication` a on a.name = r.application where a.job_opening = %(job_opening)s))"
			)
			values[f"adt{i}"] = doctype
		parts.append(
			"(log.reference_doctype = 'Application' and log.reference_name in "
			"(select name from `tabApplication` where job_opening = %(job_opening)s))"
		)
	return "(" + " or ".join(parts) + ")", values


def _where(filters):
	f = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
	conditions, values = [], {}
	if f.get("event"):
		template = frappe.db.get_value("Recruitment Email Rule", f["event"], "email_template")
		conditions.append("log.email_template = %(template)s")
		values["template"] = template or ""
	if f.get("email_template"):
		conditions.append("log.email_template = %(email_template)s")
		values["email_template"] = f["email_template"]
	if f.get("status"):
		conditions.append("log.status = %(status)s")
		values["status"] = f["status"]
	if f.get("recipient"):
		conditions.append("log.recipient like %(recipient)s")
		values["recipient"] = f"%{f['recipient'].strip()}%"
	if f.get("from_date"):
		conditions.append("log.sent_on >= %(from_date)s")
		values["from_date"] = getdate(f["from_date"])
	if f.get("to_date"):
		conditions.append("log.sent_on < %(to_date)s")
		values["to_date"] = add_to_date(getdate(f["to_date"]), days=1)
	if f.get("application"):
		# The Application ID staff see (e.g. on emails) or the record name.
		application = f["application"].strip()
		f["application"] = (
			application
			if frappe.db.exists("Application", application)
			else frappe.db.get_value("Application", {"application_id": application}, "name") or application
		)
	if f.get("job_opening") or f.get("application"):
		# An application already belongs to one job: it alone narrows enough.
		condition, more = _reference_condition(None if f.get("application") else f.get("job_opening"), f.get("application"))
		conditions.append(condition)
		values.update(more)
	return (" where " + " and ".join(conditions)) if conditions else "", values


def _enrich(rows):
	"""Event, job and application for each log row."""
	events = _events_by_template()
	by_doctype = {}
	for row in rows:
		by_doctype.setdefault(row.reference_doctype, set()).add(row.reference_name)
	links = {}
	for doctype, names in by_doctype.items():
		if not doctype or not frappe.db.exists("DocType", doctype):
			continue
		if doctype == "Application":
			for a in frappe.get_all("Application", filters={"name": ["in", list(names)]}, fields=["name", "job_opening"]):
				links[(doctype, a.name)] = {"application": a.name, "job_opening": a.job_opening}
			continue
		if doctype == "Job Opening":
			for name in names:
				links[(doctype, name)] = {"job_opening": name}
			continue
		fields = [f for f in ("application", "job_opening") if _has(doctype, f)]
		if not fields:
			continue
		for r in frappe.get_all(doctype, filters={"name": ["in", list(names)]}, fields=["name", *fields]):
			link = {f: r.get(f) for f in fields}
			if link.get("application") and not link.get("job_opening"):
				link["job_opening"] = frappe.db.get_value("Application", link["application"], "job_opening")
			links[(doctype, r.name)] = link

	apps = {l.get("application") for l in links.values() if l.get("application")}
	jobs = {l.get("job_opening") for l in links.values() if l.get("job_opening")}
	app_info = {
		a.name: a
		for a in frappe.get_all(
			"Application",
			filters={"name": ["in", list(apps) or [""]]},
			fields=["name", "application_id", "candidate.full_name as candidate_name"],
		)
	}
	job_titles = dict(frappe.get_all("Job Opening", filters={"name": ["in", list(jobs) or [""]]}, fields=["name", "job_title"], as_list=True))
	for row in rows:
		link = links.get((row.reference_doctype, row.reference_name), {})
		row.events = events.get(row.email_template, [])
		row.event_label = ", ".join(e["label"] for e in row.events) or row.email_template
		row.application = link.get("application")
		row.job_opening = link.get("job_opening")
		row.job_title = job_titles.get(row.job_opening)
		info = app_info.get(row.application)
		row.application_id = info.application_id if info else None
		row.candidate_name = info.candidate_name if info else None
	return rows


@frappe.whitelist()
def list_communications(filters=None, start=0, page_length=PAGE_LENGTH):
	"""Communication Log rows, newest first, with filters: event, job_opening,
	application, status, recipient, from_date, to_date."""
	_require_read()
	where, values = _where(filters)
	start, page_length = max(cint(start), 0), min(max(cint(page_length) or PAGE_LENGTH, 1), 500)
	rows = frappe.db.sql(
		f"""select log.name, log.reference_doctype, log.reference_name, log.email_template, log.recipient, log.sent_on, log.status
		from `tabCommunication Log` log {where}
		order by log.sent_on desc, log.creation desc
		limit {page_length} offset {start}""",
		values,
		as_dict=True,
	)
	total = frappe.db.sql(f"select count(*) from `tabCommunication Log` log {where}", values)[0][0]
	return {"rows": _enrich(rows), "total": total, "start": start, "page_length": page_length}


@frappe.whitelist()
def get_filter_options():
	_require_read()
	return {
		"events": frappe.get_all("Recruitment Email Rule", fields=["name as value", "label", "stage"], order_by="sort_order asc"),
		"statuses": ["Sent", "Failed"],
		"jobs": frappe.get_all("Job Opening", fields=["name as value", "job_title as label"], order_by="creation desc"),
	}


def _decode(value):
	try:
		return str(make_header(decode_header(value or "")))
	except Exception:
		return value or ""


def _sent_email(log):
	"""The email as queued for this recipient, if Frappe still keeps it."""
	sent_on = get_datetime(log.sent_on or log.creation)
	queues = frappe.db.sql(
		"""select q.name, q.message, q.status, q.creation, q.error
		from `tabEmail Queue` q join `tabEmail Queue Recipient` r on r.parent = q.name
		where q.reference_doctype = %s and q.reference_name = %s and r.recipient = %s
			and q.creation between %s and %s
		order by abs(timestampdiff(second, q.creation, %s)) asc limit 1""",
		(log.reference_doctype, log.reference_name, log.recipient, add_to_date(sent_on, minutes=-10), add_to_date(sent_on, minutes=10), sent_on),
		as_dict=True,
	)
	if not queues:
		return None
	queue = queues[0]
	subject, html, text = "", "", ""
	try:
		message = email.message_from_string(queue.message or "")
		subject = _decode(message.get("Subject"))
		for part in message.walk():
			if part.get_content_maintype() == "multipart" or part.get_filename():
				continue
			payload = part.get_payload(decode=True)
			if payload is None:
				continue
			body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
			if part.get_content_type() == "text/html" and not html:
				html = body
			elif part.get_content_type() == "text/plain" and not text:
				text = body
	except Exception:
		html = ""
	return {"queue": queue.name, "queue_status": queue.status, "subject": subject, "html": html, "text": text, "error": queue.error}


@frappe.whitelist()
def get_communication(name):
	"""One log row with the email as it was sent."""
	_require_read()
	log = frappe.get_doc("Communication Log", name)
	row = _enrich([frappe._dict(log.as_dict())])[0]
	row["email"] = _sent_email(log)
	if not row["email"] and log.email_template and frappe.db.exists("Email Template", log.email_template):
		# Fallback: the template as it reads now (placeholders not filled in).
		template = frappe.get_doc("Email Template", log.email_template)
		from pathways.utils.communication import template_body

		row["template"] = {"subject": template.subject, "html": template_body(template)}
	return row


@frappe.whitelist()
def list_for_application(application):
	"""Emails about one application and its interviews, offers etc., for the
	application page (needs read on the application and on the log)."""
	frappe.get_doc("Application", application).check_permission("read")
	if not frappe.has_permission("Communication Log", "read"):
		return {"rows": [], "total": 0, "can_view": False}
	data = list_communications({"application": application}, 0, 200)
	data["can_view"] = True
	return data
