# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Panel thank-you and honorarium (workflow step 33).

"Send thank-you to panel" on the consolidated score sheet emails each
Selection Committee panellist once. Only external experts are paid an
honorarium: each gets a Panel Honorarium record (the default amount from
Pathways Settings > Panel Honorarium). The recruitment team enters the
amount, PAN and bank details with the documents on the Honorarium page,
previews the email and sends it to the Finance team (the
"honorarium_to_finance" email in Email Setup). That is the end of the
process here: Pending -> Sent to Finance."""

import frappe
from frappe import _
from frappe.utils import cint, flt

DOCTYPE = "Panel Honorarium"
EVENT = "panel_thanks"
FINANCE_EVENT = "honorarium_to_finance"
# Internal panellists keep a "Not applicable" record: it only tracks their
# thank-you and is not shown on the Honorarium page.
STATUSES = ("Pending", "Sent to Finance", "Not applicable")
# Details the Finance team needs before the email can go.
REQUIRED = (
	("amount", "Amount"),
	("pan_number", "PAN"),
	("account_holder_name", "Account holder name"),
	("bank_account_number", "Account number"),
	("bank_name", "Bank name"),
	("ifsc_code", "IFSC code"),
)
DETAIL_FIELDS = (
	"amount", "pan_number", "account_holder_name", "bank_account_number", "bank_name", "bank_branch", "ifsc_code",
	"pan_card_copy", "bank_consent_form", "supporting_document", "remarks",
)
ATTACH_FIELDS = ("pan_card_copy", "bank_consent_form", "supporting_document")


def _require(ptype):
	if not frappe.has_permission(DOCTYPE, ptype):
		frappe.throw(_("You do not have access to panel honoraria."), frappe.PermissionError)


def _panel(job_opening):
	"""(committee name, [{member, is_external_expert}]) for the job's
	Selection Committee."""
	committee = frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, "name")
	if not committee:
		return None, []
	members = frappe.get_all(
		"Committee Member Row",
		filters={"parent": committee, "parenttype": "Selection Committee"},
		fields=["member", "is_external_expert"],
		order_by="idx asc",
	)
	return committee, [m for m in members if m.member]


def _default_amount():
	return flt(frappe.get_cached_doc("Pathways Settings").get("honorarium_external_amount"))


def panel_thanks_pending(job_opening):
	committee, members = _panel(job_opening)
	thanked = set(
		frappe.get_all(DOCTYPE, filters={"job_opening": job_opening, "thanks_sent_on": ["is", "set"]}, pluck="panellist")
	)
	return {
		"committee": committee,
		"panel_size": len(members),
		"pending": sum(1 for m in members if m.member not in thanked),
		"sent": sum(1 for m in members if m.member in thanked),
		"external": sum(1 for m in members if cint(m.is_external_expert)),
		"enabled": bool(frappe.db.get_value("Recruitment Email Rule", EVENT, "enabled")),
		"can_send": bool(frappe.has_permission(DOCTYPE, "create")),
	}


def _honorarium_row(job_opening, committee, member):
	"""The panellist's record for this job, created on first use: Pending
	with the default amount for an external expert, Not applicable for an
	internal panellist."""
	name = frappe.db.get_value(DOCTYPE, {"job_opening": job_opening, "panellist": member.member}, "name")
	if name:
		return frappe.get_doc(DOCTYPE, name)
	external = cint(member.is_external_expert)
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"job_opening": job_opening,
			"selection_committee": committee,
			"panellist": member.member,
			"is_external": external,
			"status": "Pending" if external else "Not applicable",
			"amount": _default_amount() if external else 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


@frappe.whitelist(methods=["POST"])
def send_panel_thanks(job_opening):
	"""Thank each panellist of the job's Selection Committee once (the
	panel_thanks email) and open their record (an honorarium only for
	external experts). Panellists already thanked are skipped, so this can be run again
	after a panellist is added."""
	_require("create")
	committee, members = _panel(job_opening)
	if not committee:
		frappe.throw(_("Job Opening {0} has no Selection Committee.").format(job_opening))
	if not frappe.db.get_value("Recruitment Email Rule", EVENT, "enabled"):
		frappe.throw(_("The 'Thank you to panellists' email is switched off in Email Setup."))
	from pathways.utils.communication import send_event

	job = frappe.db.get_value("Job Opening", job_opening, ["job_title"], as_dict=True)
	interview_date = frappe.db.get_value("Selection Committee", committee, "scheduled_date")
	thanked, created = [], 0
	for member in members:
		existed = frappe.db.exists(DOCTYPE, {"job_opening": job_opening, "panellist": member.member})
		row = _honorarium_row(job_opening, committee, member)
		created += 0 if existed else 1
		# Re-check under a row lock: a double click sends one thank-you.
		if frappe.db.get_value(DOCTYPE, row.name, "thanks_sent_on", for_update=True):
			continue
		row.db_set("thanks_sent_on", frappe.utils.now_datetime())
		send_event(
			EVENT,
			DOCTYPE,
			row.name,
			{
				"job_title": job.job_title,
				"interview_date": frappe.utils.formatdate(interview_date, "dd MMM yyyy") if interview_date else "",
				"is_external": cint(member.is_external_expert),
			},
			approvers=[member.member],
		)
		thanked.append(member.member)
	return {"sent": len(thanked), "panellists": thanked, "created": created}


@frappe.whitelist(methods=["POST"])
def sync_external_panellists():
	"""Open a record for every external expert on a Selection Committee who
	has none yet, so the Honorarium page lists them before the thank-you."""
	if not frappe.has_permission(DOCTYPE, "create"):
		return 0
	created = 0
	rows = frappe.get_all(
		"Committee Member Row",
		filters={"parenttype": "Selection Committee", "is_external_expert": 1},
		fields=["parent", "member"],
	)
	jobs = dict(frappe.get_all("Selection Committee", filters={"name": ["in", list({r.parent for r in rows}) or [""]]}, fields=["name", "job_opening"], as_list=True))
	for r in rows:
		job = jobs.get(r.parent)
		if job and r.member and not frappe.db.exists(DOCTYPE, {"job_opening": job, "panellist": r.member}):
			_honorarium_row(job, r.parent, frappe._dict(member=r.member, is_external_expert=1))
			created += 1
	return created


# ------------------------------------------------------------ Honorarium page


def missing_details(doc):
	"""Labels of the details still to enter before sending to Finance."""
	return [label for field, label in REQUIRED if (flt(doc.get(field)) <= 0 if field == "amount" else not doc.get(field))]


@frappe.whitelist()
def get_honoraria(job_opening=None, status=None):
	_require("read")
	filters = {"is_external": 1}
	if job_opening:
		filters["job_opening"] = job_opening
	if status:
		filters["status"] = status
	rows = frappe.get_all(
		DOCTYPE,
		filters=filters,
		fields=[
			"name", "job_opening", "job_title", "panellist", "panellist_name", "status", "thanks_sent_on",
			"sent_to_finance_on", "sent_to_finance_by", "creation", *DETAIL_FIELDS,
		],
		order_by="creation desc",
		limit_page_length=0,
	)
	for r in rows:
		r.sent_to_finance_by_name = frappe.utils.get_fullname(r.sent_to_finance_by) if r.sent_to_finance_by else ""
		r.missing = missing_details(r)
	return {
		"rows": rows,
		"can_write": bool(frappe.has_permission(DOCTYPE, "write")),
		"finance_email_enabled": bool(frappe.db.get_value("Recruitment Email Rule", FINANCE_EVENT, "enabled")),
	}


@frappe.whitelist(methods=["POST"])
def update_honorarium(name, **fields):
	"""Save the amount, PAN, bank details, documents and remarks entered on
	the Honorarium page. Files replaced or removed are deleted, so the
	Finance email attaches only the current ones."""
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("write")
	for field in DETAIL_FIELDS:
		if field in fields and fields[field] is not None:
			value = fields[field]
			doc.set(field, flt(value) if field == "amount" else ((value or "").strip() or None))
	doc.save()
	keep = {doc.get(f) for f in ATTACH_FIELDS if doc.get(f)}
	for f in frappe.get_all("File", filters={"attached_to_doctype": DOCTYPE, "attached_to_name": doc.name}, fields=["name", "file_url"]):
		if f.file_url not in keep:
			frappe.delete_doc("File", f.name, ignore_permissions=True)
	return doc.name


def _finance_context(doc):
	committee_date = frappe.db.get_value("Selection Committee", doc.selection_committee, "scheduled_date") if doc.selection_committee else None
	email = frappe.db.get_value("User", doc.panellist, "email") or doc.panellist
	return {
		"panellist_name": doc.panellist_name or doc.panellist,
		"panellist_email": email,
		"job_title": doc.job_title,
		"job_opening": doc.job_opening,
		"interview_date": frappe.utils.formatdate(committee_date, "dd MMM yyyy") if committee_date else "",
		"amount": frappe.utils.fmt_money(doc.amount, currency="INR"),
		"pan_number": doc.pan_number or "",
		"account_holder_name": doc.account_holder_name or "",
		"bank_account_number": doc.bank_account_number or "",
		"bank_name": doc.bank_name or "",
		"bank_branch": doc.bank_branch or "",
		"ifsc_code": doc.ifsc_code or "",
		"remarks": doc.remarks or "",
		"sent_by": frappe.utils.get_fullname(frappe.session.user),
	}


def _ready(name):
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("write")
	missing = missing_details(doc)
	if missing:
		frappe.throw(_("{0}: enter {1} before sending to Finance.").format(doc.panellist_name or doc.panellist, ", ".join(missing)))
	return doc


@frappe.whitelist()
def preview_finance_email(name):
	"""The honorarium_to_finance email as Send would send it. To / CC come
	from Email Setup; the page lets them (and BCC) be changed before sending."""
	from pathways.utils.communication import preview_event

	doc = _ready(name)
	preview = preview_event(FINANCE_EVENT, DOCTYPE, doc.name, _finance_context(doc))
	preview["can_remember"] = bool(frappe.has_permission("Recruitment Email Rule", "write"))
	return preview


@frappe.whitelist(methods=["POST"])
def send_to_finance(names, to=None, cc=None, bcc=None, remember=0):
	"""Email each record's details and documents to the Finance team (one
	email per external expert, to exactly the To / CC / BCC given; Email
	Setup's when not given) and mark it Sent to Finance. remember=1 saves
	To and CC as the defaults in Email Setup."""
	from pathways.utils.communication import _event_parts, _render_event, parse_emails

	rule = frappe.get_doc("Recruitment Email Rule", FINANCE_EVENT)
	if not rule.enabled:
		frappe.throw(_("The 'Honorarium details to Finance' email is switched off in Email Setup."))
	defaults = _event_parts(FINANCE_EVENT)
	to = parse_emails(to) if to is not None else [e for e, _n in defaults.recipients]
	cc = parse_emails(cc) if cc is not None else defaults.cc
	bcc = parse_emails(bcc)
	if not to:
		frappe.throw(_("Enter the Finance team's email address in To."))
	if cint(remember):
		rule.check_permission("write")
		rule.extra_recipients = ", ".join(to)
		rule.cc = ", ".join(cc)
		rule.save()

	names = frappe.parse_json(names) if isinstance(names, str) else names
	sent, skipped = [], []
	for name in names or []:
		doc = frappe.get_doc(DOCTYPE, name)
		doc.check_permission("write")
		missing = missing_details(doc)
		if missing:
			skipped.append(_("{0}: enter {1}").format(doc.panellist_name or doc.panellist, ", ".join(missing)))
			continue
		parts = _event_parts(FINANCE_EVENT, DOCTYPE, doc.name)
		subject, message = _render_event(parts, _finance_context(doc), to[0], "")
		frappe.sendmail(
			recipients=to,
			cc=cc,
			bcc=[e for e in bcc if e.lower() not in {x.lower() for x in to + cc}],
			subject=subject,
			message=message,
			reference_doctype=DOCTYPE,
			reference_name=doc.name,
			attachments=[{"fid": f} for f in parts.files] or None,
			reply_to=parts.reply_to,
		)
		for email in to:
			frappe.get_doc(
				{
					"doctype": "Communication Log",
					"reference_doctype": DOCTYPE,
					"reference_name": doc.name,
					"email_template": rule.email_template,
					"recipient": email,
					"sent_on": frappe.utils.now_datetime(),
					"status": "Sent",
				}
			).insert(ignore_permissions=True)
		doc.status = "Sent to Finance"
		doc.sent_to_finance_on = frappe.utils.now_datetime()
		doc.sent_to_finance_by = frappe.session.user
		doc.save()
		sent.append(name)
	return {"sent": len(sent), "skipped": skipped}


@frappe.whitelist()
def export_honoraria(job_opening=None, status=None):
	"""The list as Excel."""
	from io import BytesIO

	from openpyxl import Workbook
	from openpyxl.styles import Font

	data = get_honoraria(job_opening, status)
	wb = Workbook()
	ws = wb.active
	ws.title = "Panel Honorarium"
	head = [
		"Position", "Job Opening", "External Expert", "Email", "Amount", "PAN", "Account Holder", "Account Number", "Bank", "Branch",
		"IFSC", "Status", "Sent to Finance On", "Sent By", "Thanked On", "Remarks",
	]
	ws.append(head)
	for cell in ws[1]:
		cell.font = Font(bold=True)
	for r in data["rows"]:
		ws.append(
			[
				r.job_title, r.job_opening, r.panellist_name, r.panellist, flt(r.amount), r.pan_number or "", r.account_holder_name or "",
				r.bank_account_number or "", r.bank_name or "", r.bank_branch or "", r.ifsc_code or "", r.status,
				frappe.utils.format_datetime(r.sent_to_finance_on) if r.sent_to_finance_on else "", r.sent_to_finance_by_name,
				frappe.utils.format_datetime(r.thanks_sent_on) if r.thanks_sent_on else "", r.remarks or "",
			]
		)
	for col, width in zip("ABCDEFGHIJKLMNOP", (30, 18, 24, 28, 12, 13, 24, 20, 22, 18, 13, 16, 18, 20, 18, 30)):
		ws.column_dimensions[col].width = width
	buffer = BytesIO()
	wb.save(buffer)
	frappe.local.response.filename = "Panel Honorarium.xlsx"
	frappe.local.response.filecontent = buffer.getvalue()
	frappe.local.response.type = "download"
