# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Panel thank-you and honorarium (workflow step 33).

"Send thank-you to panel" on the consolidated score sheet emails each
Selection Committee panellist once and opens a Panel Honorarium record for
them, with the default amount from Pathways Settings > Panel Honorarium.
The Honorarium page then takes each record through Pending -> Approved ->
Paid (or Not applicable). Who may approve is the "Honorarium Approver
Roles" table in Pathways Settings; everything else is Role Permissions on
Panel Honorarium."""

import frappe
from frappe import _
from frappe.utils import cint, flt

from pathways.pathways.doctype.panel_honorarium.panel_honorarium import can_approve

DOCTYPE = "Panel Honorarium"
EVENT = "panel_thanks"
STATUSES = ("Pending", "Approved", "Paid", "Not applicable")


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


def _settings():
	s = frappe.get_cached_doc("Pathways Settings")
	return {
		"internal": flt(s.get("honorarium_internal_amount")),
		"external": flt(s.get("honorarium_external_amount")),
		"external_only": cint(s.get("honorarium_external_only")),
	}


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
		"enabled": bool(frappe.db.get_value("Recruitment Email Rule", EVENT, "enabled")),
		"external_only": _settings()["external_only"],
		"can_send": bool(frappe.has_permission(DOCTYPE, "create")),
	}


def _honorarium_row(job_opening, committee, member, settings):
	"""The panellist's honorarium record for this job, created on first use."""
	name = frappe.db.get_value(DOCTYPE, {"job_opening": job_opening, "panellist": member.member}, "name")
	if name:
		return frappe.get_doc(DOCTYPE, name)
	external = cint(member.is_external_expert)
	applicable = external or not settings["external_only"]
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"job_opening": job_opening,
			"selection_committee": committee,
			"panellist": member.member,
			"is_external": external,
			"status": "Pending" if applicable else "Not applicable",
			"amount": (settings["external"] if external else settings["internal"]) if applicable else 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


@frappe.whitelist(methods=["POST"])
def send_panel_thanks(job_opening):
	"""Thank each panellist of the job's Selection Committee once (the
	panel_thanks email) and open their honorarium record. Panellists already
	thanked are skipped, so this can be run again after a panellist is added."""
	_require("create")
	committee, members = _panel(job_opening)
	if not committee:
		frappe.throw(_("Job Opening {0} has no Selection Committee.").format(job_opening))
	if not frappe.db.get_value("Recruitment Email Rule", EVENT, "enabled"):
		frappe.throw(_("The 'Thank you to panellists' email is switched off in Email Setup."))
	from pathways.utils.communication import send_event

	settings = _settings()
	job = frappe.db.get_value("Job Opening", job_opening, ["job_title"], as_dict=True)
	interview_date = frappe.db.get_value("Selection Committee", committee, "scheduled_date")
	thanked, created = [], 0
	for member in members:
		existed = frappe.db.exists(DOCTYPE, {"job_opening": job_opening, "panellist": member.member})
		row = _honorarium_row(job_opening, committee, member, settings)
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


# ------------------------------------------------------------ Honorarium page


@frappe.whitelist()
def get_honoraria(job_opening=None, status=None):
	_require("read")
	filters = {}
	if job_opening:
		filters["job_opening"] = job_opening
	if status:
		filters["status"] = status
	rows = frappe.get_all(
		DOCTYPE,
		filters=filters,
		fields=[
			"name", "job_opening", "job_title", "panellist", "panellist_name", "is_external", "status", "amount",
			"pan_number", "bank_consent_form", "thanks_sent_on", "approved_by", "approved_on", "paid_on",
			"payment_reference", "remarks", "creation",
		],
		order_by="creation desc",
		limit_page_length=0,
	)
	for r in rows:
		r.approved_by_name = frappe.utils.get_fullname(r.approved_by) if r.approved_by else ""
		r.is_external = cint(r.is_external)
	return {
		"rows": rows,
		"can_approve": can_approve(),
		"can_write": bool(frappe.has_permission(DOCTYPE, "write")),
	}


def _each(names, fn):
	names = frappe.parse_json(names) if isinstance(names, str) else names
	done, skipped = [], []
	for name in names or []:
		doc = frappe.get_doc(DOCTYPE, name)
		doc.check_permission("write")
		reason = fn(doc)
		if reason:
			skipped.append(f"{doc.panellist_name or doc.panellist}: {reason}")
			continue
		doc.save()
		done.append(name)
	return {"updated": len(done), "skipped": skipped}


@frappe.whitelist(methods=["POST"])
def approve(names):
	if not can_approve():
		frappe.throw(_("You are not an honorarium approver (Pathways Settings > Panel Honorarium)."), frappe.PermissionError)

	def fn(doc):
		if doc.status != "Pending":
			return _("is {0}").format(_(doc.status))
		if flt(doc.amount) <= 0:
			return _("no amount")
		doc.status = "Approved"

	return _each(names, fn)


@frappe.whitelist(methods=["POST"])
def mark_paid(names, paid_on=None, payment_reference=None):
	def fn(doc):
		if doc.status != "Approved":
			return _("is {0}, not Approved").format(_(doc.status))
		doc.status = "Paid"
		doc.paid_on = paid_on or frappe.utils.today()
		if payment_reference:
			doc.payment_reference = payment_reference

	return _each(names, fn)


@frappe.whitelist(methods=["POST"])
def update_honorarium(name, amount=None, pan_number=None, bank_consent_form=None, remarks=None, not_applicable=None):
	"""Edit a record's details from the Honorarium page. The amount can
	only change before approval; not_applicable=1/0 takes a Pending record
	out of (or back into) the payment run."""
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("write")
	if amount is not None and flt(amount) != flt(doc.amount):
		if doc.status not in ("Pending", "Not applicable"):
			frappe.throw(_("The amount cannot change after approval."))
		doc.amount = flt(amount)
	if not_applicable is not None:
		if doc.status not in ("Pending", "Not applicable"):
			frappe.throw(_("Only a pending honorarium can be marked not applicable."))
		doc.status = "Not applicable" if cint(not_applicable) else "Pending"
	for field, value in (("pan_number", pan_number), ("bank_consent_form", bank_consent_form), ("remarks", remarks)):
		if value is not None:
			doc.set(field, value or None)
	doc.save()
	return doc.name


@frappe.whitelist()
def export_honoraria(job_opening=None, status=None):
	"""The list as Excel, for the finance team's payment run."""
	from io import BytesIO

	from openpyxl import Workbook
	from openpyxl.styles import Font

	data = get_honoraria(job_opening, status)
	wb = Workbook()
	ws = wb.active
	ws.title = "Panel Honorarium"
	head = [
		"Position", "Job Opening", "Panellist", "Email", "External", "Amount", "Status", "PAN", "Thanked On",
		"Approved By", "Approved On", "Paid On", "Payment Reference", "Bank / Consent Form", "Remarks",
	]
	ws.append(head)
	for cell in ws[1]:
		cell.font = Font(bold=True)
	site = frappe.utils.get_url()
	for r in data["rows"]:
		ws.append(
			[
				r.job_title, r.job_opening, r.panellist_name, r.panellist, "Yes" if r.is_external else "No", flt(r.amount), r.status,
				r.pan_number or "", frappe.utils.format_datetime(r.thanks_sent_on) if r.thanks_sent_on else "", r.approved_by_name,
				frappe.utils.format_datetime(r.approved_on) if r.approved_on else "", frappe.utils.formatdate(r.paid_on) if r.paid_on else "",
				r.payment_reference or "", f"{site}{r.bank_consent_form}" if r.bank_consent_form else "", r.remarks or "",
			]
		)
	for col, width in zip("ABCDEFGHIJKLMNO", (30, 18, 24, 28, 9, 12, 14, 13, 18, 20, 18, 12, 20, 40, 30)):
		ws.column_dimensions[col].width = width
	buffer = BytesIO()
	wb.save(buffer)
	frappe.local.response.filename = "Panel Honorarium.xlsx"
	frappe.local.response.filecontent = buffer.getvalue()
	frappe.local.response.type = "download"
