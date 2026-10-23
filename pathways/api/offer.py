# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Offers and appointment orders (workflow steps 22, 23 and 26-29).

Staff: create a draft from a selected application, fill in the letter
details, submit it for review, approve or return it (Offer Reviewer Roles),
sign it (Offer Signatory Roles), send it, and file the scanned signed copy.
Candidate: see the sent letter, download it, accept or decline and upload
the signed acceptance copy.

Who reviews and who signs is configured in Pathways Settings (role tables),
never in code. Every endpoint checks the record's permission first, which
keeps candidates to their own offers (pathways.permissions.has_offer_permission),
and every status change is a normal save() so doc_events hooks fire.
"""

import base64
import mimetypes

import frappe
from frappe import _
from frappe.utils import add_days, cint, escape_html, fmt_money, formatdate, get_url, getdate, now_datetime, today

from pathways.pathways.doctype.offer_appointment_order.offer_appointment_order import (
	CANDIDATE_VISIBLE_STATUSES,
	DRAFT_STATUSES,
	find_approved_green_sheet,
	green_sheet_required,
)
from pathways.pathways.doctype.offer_appointment_order.offer_appointment_order import (
	respond_to_offer as _respond_to_offer,
)
from pathways.permissions import has_duty, has_full_access
from pathways.utils.communication import candidate_email_context, send_event
from pathways.utils.letterhead import letterhead_html

DOCTYPE = "Offer Appointment Order"

# Fields staff fill in while the offer is a draft.
EDITABLE_FIELDS = (
	"appointment_order_template",
	"reference_number",
	"designation",
	"department",
	"employment_type",
	"place_of_posting",
	"reporting_to",
	"proposed_doj",
	"probation_period",
	"contract_period",
	"contract_end_date",
	"pay_level",
	"pay_scale",
	"consolidated_fee",
	"gross_monthly_salary",
	"allowances",
	"compensation_remarks",
	"verbal_offer_date",
	"verbal_offer_by",
	"verbal_offer_compensation",
	"verbal_offer_notes",
	"terms",
	"acceptance_deadline",
)
# What must be filled before review: enough for a complete letter.
REQUIRED_FOR_REVIEW = ("appointment_order_template", "designation", "proposed_doj")
COMPENSATION_FIELDS = ("pay_level", "pay_scale", "consolidated_fee", "gross_monthly_salary")
MAX_SIGNATURE_BYTES = 1024 * 1024


# ----------------------------------------------------------------- helpers


def _get(name, ptype="read"):
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission(ptype)
	return doc


def _is_staff():
	return has_full_access(DOCTYPE)


def _require_staff():
	if not _is_staff():
		frappe.throw(_("You are not permitted to manage offers."), frappe.PermissionError)


def can_review():
	return has_duty("offer_reviewer_roles")


def can_sign():
	return has_duty("offer_signatory_roles")


def _duty_users(settings_field):
	roles = [row.role for row in frappe.get_cached_doc("Pathways Settings").get(settings_field) or [] if row.role]
	if not roles:
		return []
	return frappe.get_all(
		"User",
		filters=[["Has Role", "role", "in", roles], ["enabled", "=", 1], ["name", "not in", ("Administrator", "Guest")]],
		pluck="name",
		distinct=True,
	)


def _save(doc, action, remarks=None):
	"""Status changes by duty holders: the duty is checked by the caller, so
	the save itself does not also need the DocType write permission."""
	doc.flags.offer_action = action
	doc.flags.offer_remarks = remarks
	doc.flags.ignore_permissions = True
	doc.save()


def _notify(event, doc, users, **extra):
	if not users:
		return
	job_title = frappe.db.get_value("Job Opening", doc.job_opening, "job_title") if doc.job_opening else ""
	context = {
		"offer_name": doc.name,
		"candidate_name": doc.candidate_name,
		"job_title": job_title,
		"designation": doc.designation,
		"status": doc.status,
		"link": get_url(f"/pathways/offers/{doc.name}"),
		**extra,
	}
	send_event(event, DOCTYPE, doc.name, context, approvers=users)


def _fmt_date(value):
	return formatdate(value, "dd MMMM yyyy") if value else ""


def _money(value):
	return fmt_money(value, currency="INR", precision=0) if value else ""


def claim_file(file_url, offer, fieldname):
	"""Attach a file the session user just uploaded to the offer field.
	Only files the user owns (or that already belong to this offer) can be
	claimed, so nobody can point an offer at someone else's file."""
	if not file_url:
		return None
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name", order_by="creation desc")
	if not file_name:
		frappe.throw(_("The uploaded file could not be found. Please upload it again."))
	file = frappe.get_doc("File", file_name)
	attached_here = file.attached_to_doctype == DOCTYPE and file.attached_to_name == offer.name
	if not attached_here:
		if file.attached_to_doctype or (file.owner != frappe.session.user and frappe.session.user != "Administrator"):
			frappe.throw(_("This file cannot be used here. Please upload it again."), frappe.PermissionError)
		file.attached_to_doctype = DOCTYPE
		file.attached_to_name = offer.name
		file.attached_to_field = fieldname
		file.is_private = 1
		file.flags.ignore_permissions = True
		file.save()
	return file.file_url


# ------------------------------------------------------------ the letter


def _file_data_url(file_url):
	"""Embed an image as a data: URL. wkhtmltopdf cannot fetch private
	files (they need a login), and an embedded copy keeps the signed letter
	unchanged even if the saved signature is replaced later."""
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		return None
	file = frappe.get_doc("File", file_name)
	content = file.get_content()
	if isinstance(content, str):
		content = content.encode()
	mime = mimetypes.guess_type(file.file_name or file_url)[0] or "image/png"
	return f"data:{mime};base64,{base64.b64encode(content).decode()}"


def letter_context(offer):
	"""Values a template can use (listed on its Letter Body field)."""
	app = frappe.get_doc("Application", offer.application)
	context, _candidate = candidate_email_context(app)
	address = frappe.db.get_value("Candidate", app.candidate, "address") or ""
	settings = frappe.get_cached_doc("Pathways Settings")
	# Candidate-typed values are escaped; staff-written terms stay HTML.
	safe = {k: escape_html(v) if isinstance(v, str) else v for k, v in context.items()}
	safe.update(
		{
			"candidate_address": escape_html(address).replace("\n", "<br>"),
			"offer_name": offer.name,
			"reference_number": escape_html(offer.reference_number or offer.name),
			"designation": offer.designation or "",
			"department": offer.department or "",
			"employment_type": offer.employment_type or "",
			"place_of_posting": escape_html(offer.place_of_posting or ""),
			"reporting_to": escape_html(offer.reporting_to or ""),
			"proposed_doj": _fmt_date(offer.proposed_doj),
			"probation_period": escape_html(offer.probation_period or ""),
			"contract_period": escape_html(offer.contract_period or ""),
			"contract_end_date": _fmt_date(offer.contract_end_date),
			"pay_level": escape_html(offer.pay_level or ""),
			"pay_scale": escape_html(offer.pay_scale or ""),
			"consolidated_fee": _money(offer.consolidated_fee),
			"gross_monthly_salary": _money(offer.gross_monthly_salary),
			"allowances": escape_html(offer.allowances or ""),
			"terms": offer.terms or "",
			"offer_date": _fmt_date(offer.offer_date if offer.status in CANDIDATE_VISIBLE_STATUSES else today()),
			"acceptance_deadline": _fmt_date(
				offer.acceptance_deadline or add_days(today(), cint(settings.acceptance_deadline_days) or 7)
			),
			"signatory_title": offer.signatory_title or settings.get("offer_signatory_title") or "Registrar",
		}
	)
	return safe


LETTER_WRAPPER = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body { font-family: "Times New Roman", Georgia, serif; font-size: 12pt; color: #111; line-height: 1.45; }
.head { text-align: center; border-bottom: 2px solid #3a2a6b; padding-bottom: 8px; margin-bottom: 14px; }
.head .org { font-size: 17pt; font-weight: bold; letter-spacing: .5px; }
.head .sub { font-size: 10pt; color: #444; }
.meta { width: 100%; font-size: 11pt; margin-bottom: 12px; }
.meta td { padding: 0; }
ol li { margin-bottom: 6px; }
.sign { margin-top: 28px; }
.sign img { max-height: 70px; max-width: 220px; display: block; }
.pending { display: inline-block; border: 1px dashed #999; color: #888; padding: 14px 24px; font-size: 10pt; }
.draft { color: #b45309; font-size: 10pt; text-align: right; }
</style></head>
<body>
{% if watermark %}<div class="draft">{{ watermark }}</div>{% endif %}
{{ letterhead }}
<table class="meta"><tr><td>Ref: {{ reference_number }}</td><td style="text-align:right">Date: {{ offer_date }}</td></tr></table>
{{ body }}
<div class="sign">
 <div>Yours sincerely,</div>
 {% if signature %}<img src="{{ signature }}" alt="Signature">{% else %}<div class="pending">Signature pending</div>{% endif %}
 {% if signed_by_name %}<div><b>{{ signed_by_name }}</b></div>{% endif %}
 <div>{{ signatory_title }}</div>
 {% if signed_on %}<div style="font-size:9pt;color:#555">Digitally signed on {{ signed_on }}</div>{% endif %}
</div>
</body></html>"""


def render_letter(offer):
	if not offer.appointment_order_template:
		frappe.throw(_("Choose an Appointment Order Template first."))
	body_template = frappe.db.get_value("Appointment Order Template", offer.appointment_order_template, "letter_body") or ""
	context = letter_context(offer)
	try:
		body = frappe.render_template(body_template, context)
	except Exception as e:
		frappe.throw(_("The template {0} could not be filled in: {1}").format(offer.appointment_order_template, e))
	signed = offer.status in ("Signed by Registrar", *CANDIDATE_VISIBLE_STATUSES)
	return frappe.render_template(
		LETTER_WRAPPER,
		{
			**context,
			"letterhead": letterhead_html(offer),
			"body": body,
			"signature": offer.registrar_signature if signed else None,
			"signed_by_name": escape_html(offer.signed_by_name or "") if signed else "",
			"signed_on": frappe.utils.format_datetime(offer.signed_on, "dd MMM yyyy, h:mm a") if signed and offer.signed_on else "",
			"watermark": "" if signed else _("DRAFT - {0}").format(offer.status),
		},
	)


def letter_pdf(offer):
	from frappe.utils.pdf import get_pdf

	return get_pdf(
		render_letter(offer),
		{"page-size": "A4", "margin-top": "18mm", "margin-bottom": "18mm", "margin-left": "20mm", "margin-right": "20mm"},
	)


def attach_letter_pdf(offer):
	"""Store the letter as a private File on the offer (replacing the
	previous one), so it is kept with the record and the appointment_order
	email attaches it (its rule has "attach record files")."""
	content = letter_pdf(offer)
	if offer.letter_pdf:
		for old in frappe.get_all(
			"File",
			filters={"attached_to_doctype": DOCTYPE, "attached_to_name": offer.name, "file_url": offer.letter_pdf},
			pluck="name",
		):
			frappe.delete_doc("File", old, ignore_permissions=True, force=True)
	file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"Appointment Order - {offer.name}.pdf",
			"content": content,
			"is_private": 1,
			"attached_to_doctype": DOCTYPE,
			"attached_to_name": offer.name,
			"attached_to_field": "letter_pdf",
		}
	)
	file.flags.ignore_permissions = True
	file.insert()
	offer.letter_pdf = file.file_url
	return file


# ------------------------------------------------------------ staff: list


@frappe.whitelist()
def get_offers():
	"""Offers list (status tabs and filters are client-side)."""
	_require_staff()
	rows = frappe.get_list(
		DOCTYPE,
		fields=[
			"name", "application", "candidate_name", "job_opening", "designation", "status", "offer_date",
			"acceptance_deadline", "proposed_doj", "candidate_confirmed_doj", "modified",
		],
		order_by="modified desc",
		limit_page_length=0,
	)
	jobs = {r.job_opening for r in rows if r.job_opening}
	titles = dict(frappe.get_all("Job Opening", filters={"name": ["in", list(jobs)]}, fields=["name", "job_title"], as_list=True)) if jobs else {}
	app_ids = {r.application for r in rows}
	ids = dict(frappe.get_all("Application", filters={"name": ["in", list(app_ids)]}, fields=["name", "application_id"], as_list=True)) if app_ids else {}
	for r in rows:
		r["job_title"] = titles.get(r.job_opening, "")
		r["application_id"] = ids.get(r.application) or r.application
		# Old statuses read as Draft.
		r["stage"] = "Draft" if r.status in DRAFT_STATUSES else r.status
	return {"offers": rows, "can_create": bool(frappe.has_permission(DOCTYPE, "create"))}


@frappe.whitelist()
def get_offer_candidates():
	"""Applications that can get an offer now: on an approved Post-Interview
	Green Sheet (or Selected, when Settings relaxes the green sheet) and
	without an offer yet. Feeds the Create offer dialog."""
	_require_staff()
	have_offer = set(frappe.get_all(DOCTYPE, pluck="application"))
	names = set()
	if frappe.db.exists("DocType", "Post-Interview Green Sheet"):
		meta = frappe.get_meta("Post-Interview Green Sheet")
		fields = [f for f in ("recommended_application", "waitlist_application") if meta.has_field(f)]
		for sheet in frappe.get_all("Post-Interview Green Sheet", filters={"status": "Approved", "docstatus": 1}, fields=fields):
			names |= {sheet.get(f) for f in fields if sheet.get(f)}
	if not green_sheet_required():
		names |= set(frappe.get_all("Application", filters={"status": "Selected"}, pluck="name"))
	names -= have_offer
	names.discard(None)
	if not names:
		return []
	apps = frappe.get_list(
		"Application",
		filters={"name": ["in", list(names)]},
		fields=["name", "application_id", "candidate", "job_opening", "status"],
	)
	for a in apps:
		a["candidate_name"] = frappe.db.get_value("Candidate", a.candidate, "full_name")
		a["job_title"] = frappe.db.get_value("Job Opening", a.job_opening, "job_title")
	return apps


@frappe.whitelist()
def get_offer_for_application(application):
	"""ApplicationDetail's Offer card: the existing offer, or whether one can
	be created for this application."""
	frappe.get_doc("Application", application).check_permission("read")
	if not _is_staff():
		return {"offer": None, "can_create": False}
	offer = frappe.db.get_value(DOCTYPE, {"application": application}, ["name", "status"], as_dict=True)
	if offer:
		return {"offer": offer, "can_create": False}
	sheet = find_approved_green_sheet(application)
	allowed = bool(frappe.has_permission(DOCTYPE, "create"))
	eligible = bool(sheet) or not green_sheet_required()
	return {
		"offer": None,
		"can_create": allowed and eligible,
		"green_sheet": sheet,
		"blocked_reason": "" if eligible else _("Needs an approved Post-Interview Green Sheet naming this candidate."),
	}


def _suggest_template(track, employment_type, designation):
	"""Best active template: designation listed > track and type both match
	> type matches > track matches > any."""
	templates = frappe.get_all(
		"Appointment Order Template", filters={"is_active": 1}, fields=["name", "track", "employment_type"], order_by="name asc"
	)
	if not templates:
		return None
	listed = set(
		frappe.get_all(
			"Appointment Order Template Designation",
			filters={"parenttype": "Appointment Order Template", "designation": designation or ""},
			pluck="parent",
		)
	)

	def score(t):
		s = 0
		if t.name in listed:
			s += 8
		if t.employment_type and t.employment_type == employment_type:
			s += 4
		elif t.employment_type:
			s -= 4
		if t.track and t.track == track:
			s += 2
		elif t.track:
			s -= 2
		return s

	return max(templates, key=score).name


@frappe.whitelist(methods=["POST"])
def create_offer(application, data=None):
	"""Draft offer for a selected application (workflow step 26). The
	green-sheet gate is enforced by the DocType controller."""
	if not frappe.has_permission(DOCTYPE, "create"):
		frappe.throw(_("You are not permitted to create offers."), frappe.PermissionError)
	frappe.get_doc("Application", application).check_permission("read")
	existing = frappe.db.get_value(DOCTYPE, {"application": application}, "name")
	if existing:
		frappe.throw(_("This application already has an offer ({0}).").format(existing))
	data = frappe.parse_json(data) if data else {}

	app = frappe.db.get_value("Application", application, ["job_opening", "track"], as_dict=True)
	job = frappe.db.get_value(
		"Job Opening", app.job_opening, ["designation", "department", "employment_type", "pay_level", "track"], as_dict=True
	) or frappe._dict()
	doc = frappe.new_doc(DOCTYPE)
	doc.application = application
	doc.status = "Draft"
	doc.designation = job.designation
	doc.department = job.department
	doc.employment_type = job.employment_type
	doc.pay_level = job.pay_level
	doc.update({k: v for k, v in data.items() if k in EDITABLE_FIELDS})
	if not doc.appointment_order_template:
		doc.appointment_order_template = _suggest_template(job.track or app.track, doc.employment_type, doc.designation)
	doc.flags.offer_action = _("Draft created")
	doc.insert()
	return doc.name


@frappe.whitelist(methods=["POST"])
def update_offer(name, data):
	doc = _get(name, "write")
	if doc.status not in DRAFT_STATUSES:
		frappe.throw(_("Only a draft can be edited. Ask the reviewer or signatory to return it for changes."))
	data = frappe.parse_json(data) if isinstance(data, str) else data or {}
	doc.update({k: v for k, v in data.items() if k in EDITABLE_FIELDS})
	if doc.status != "Draft":
		# Old "Verbal Offer" / "Drafted" records join the new flow here.
		doc.status = "Draft"
	doc.save()
	return get_offer(name)


# --------------------------------------------------------- staff: detail


def _timeline(doc):
	return [
		{
			"from_status": r.from_status,
			"to_status": r.to_status,
			"action": r.action,
			"user": r.user,
			"user_name": frappe.utils.get_fullname(r.user) if r.user else "",
			"timestamp": r.timestamp,
			"remarks": r.remarks,
		}
		for r in reversed(doc.status_log or [])
	]


@frappe.whitelist()
def get_offer(name):
	doc = _get(name)
	_require_staff()
	app = frappe.db.get_value(
		"Application", doc.application, ["name", "application_id", "candidate", "job_opening", "status"], as_dict=True
	)
	candidate = frappe.db.get_value("Candidate", app.candidate, ["full_name", "email", "mobile_number"], as_dict=True) or {}
	settings = frappe.get_cached_doc("Pathways Settings")
	can_write = bool(frappe.has_permission(DOCTYPE, "write", doc))
	is_draft = doc.status in DRAFT_STATUSES
	out = doc.as_dict(no_default_fields=False)
	out.pop("status_log", None)
	out.update(
		{
			"stage": "Draft" if is_draft else doc.status,
			"application_id": app.application_id,
			"application_status": app.status,
			"candidate_email": candidate.get("email"),
			"candidate_mobile": candidate.get("mobile_number"),
			"job_title": frappe.db.get_value("Job Opening", app.job_opening, "job_title"),
			"green_sheet_required": green_sheet_required(),
			"timeline": _timeline(doc),
			"has_saved_signature": bool(settings.get("registrar_signature_image")),
			"perms": {
				"can_edit": can_write and is_draft,
				"can_submit": can_write and is_draft,
				"can_review": doc.status == "Under Review" and can_review(),
				"can_sign": doc.status == "Approved for Signature" and can_sign(),
				"can_return": (doc.status == "Under Review" and can_review())
				or (doc.status == "Approved for Signature" and (can_sign() or can_review())),
				"can_send": can_write and doc.status == "Signed by Registrar",
				"can_upload_scan": can_write and doc.status in CANDIDATE_VISIBLE_STATUSES,
				"can_upload_signed_copy": can_write and doc.status in ("Sent", "Accepted"),
				"can_delete": bool(frappe.has_permission(DOCTYPE, "delete", doc)) and is_draft,
			},
		}
	)
	return out


@frappe.whitelist()
def get_templates():
	"""Active templates for the draft form."""
	_require_staff()
	return frappe.get_all(
		"Appointment Order Template",
		filters={"is_active": 1},
		fields=["name", "track", "employment_type", "description"],
		order_by="name asc",
	)


@frappe.whitelist()
def get_form_options():
	"""Choices for the draft form's link fields (active masters only)."""
	_require_staff()
	return {
		"templates": get_templates(),
		"designations": frappe.get_all("Designation", filters={"is_active": 1}, pluck="name", order_by="name asc"),
		"departments": frappe.get_all("Pathways Department", filters={"is_active": 1}, pluck="name", order_by="name asc"),
	}


@frappe.whitelist(methods=["POST"])
def submit_for_review(name):
	doc = _get(name, "write")
	if doc.status not in DRAFT_STATUSES:
		frappe.throw(_("Only a draft can be submitted for review."))
	missing = [doc.meta.get_label(f) for f in REQUIRED_FOR_REVIEW if not doc.get(f)]
	if not any(doc.get(f) for f in COMPENSATION_FIELDS):
		missing.append(_("Pay level, pay scale, consolidated fee or gross monthly salary"))
	if missing:
		frappe.throw(_("Fill in before review: {0}.").format(", ".join(missing)), title=_("Offer Incomplete"))
	render_letter(doc)  # surfaces template errors now rather than at signing
	doc.status = "Under Review"
	doc.submitted_for_review_by = frappe.session.user
	doc.submitted_for_review_on = now_datetime()
	_save(doc, _("Submitted for review"))
	_notify("offer_review_requested", doc, _duty_users("offer_reviewer_roles"))
	return get_offer(name)


@frappe.whitelist(methods=["POST"])
def approve_offer(name, remarks=None):
	"""Reviewer (Assistant Manager PNC): the draft is ready for signature."""
	doc = _get(name)
	if doc.status != "Under Review":
		frappe.throw(_("This offer is not under review (status: {0}).").format(doc.status))
	if not can_review():
		frappe.throw(_("Only the Offer Reviewer Roles in Pathways Settings can approve an appointment order."), frappe.PermissionError)
	doc.status = "Approved for Signature"
	doc.reviewed_by = frappe.session.user
	doc.reviewed_on = now_datetime()
	doc.review_remarks = remarks
	_save(doc, _("Approved for signature"), remarks)
	_notify("offer_signature_requested", doc, _duty_users("offer_signatory_roles"))
	return get_offer(name)


@frappe.whitelist(methods=["POST"])
def return_offer(name, remarks):
	"""Back to Draft for changes, from review (reviewer) or from signing
	(signatory, or the reviewer taking it back)."""
	doc = _get(name)
	if not (remarks or "").strip():
		frappe.throw(_("Please say what needs to change."))
	if doc.status == "Under Review":
		allowed = can_review()
	elif doc.status == "Approved for Signature":
		allowed = can_sign() or can_review()
	else:
		frappe.throw(_("Only an offer under review or awaiting signature can be returned."))
	if not allowed:
		frappe.throw(_("You cannot return this appointment order."), frappe.PermissionError)
	stage = doc.status
	doc.status = "Draft"
	doc.review_remarks = remarks
	_save(doc, _("Returned for changes at {0}").format(_("review") if stage == "Under Review" else _("signing")), remarks)
	_notify("offer_returned", doc, [doc.submitted_for_review_by or doc.owner], remarks=remarks)
	return get_offer(name)


def _check_signature(signature):
	if not signature or not isinstance(signature, str) or not signature.startswith("data:image/"):
		frappe.throw(_("Please draw your signature, or use the saved signature."))
	if len(signature) > MAX_SIGNATURE_BYTES * 4 / 3:
		frappe.throw(_("The signature image is too large."))


@frappe.whitelist(methods=["POST"])
def sign_offer(name, signature=None, use_saved_signature=0, save_as_default=0):
	"""Registrar signs (workflow step 27): a drawn signature or the saved
	signature image from Pathways Settings. The image is embedded in the
	letter, the signatory and time are stamped and the signed PDF is stored."""
	doc = _get(name)
	if doc.status != "Approved for Signature":
		frappe.throw(_("This offer is not awaiting signature (status: {0}).").format(doc.status))
	if not can_sign():
		frappe.throw(_("Only the Offer Signatory Roles in Pathways Settings can sign an appointment order."), frappe.PermissionError)

	settings = frappe.get_cached_doc("Pathways Settings")
	if cint(use_saved_signature):
		if not settings.get("registrar_signature_image"):
			frappe.throw(_("No saved signature in Pathways Settings. Draw the signature instead."))
		signature = _file_data_url(settings.registrar_signature_image)
		if not signature:
			frappe.throw(_("The saved signature image could not be read. Upload it again in Pathways Settings."))
		doc.signature_source = "Saved Signature"
	else:
		_check_signature(signature)
		doc.signature_source = "Drawn"
		if cint(save_as_default):
			save_signature(signature)

	doc.registrar_signature = signature
	doc.signed_by = frappe.session.user
	doc.signed_by_name = frappe.utils.get_fullname(frappe.session.user)
	doc.signatory_title = settings.get("offer_signatory_title") or "Registrar"
	doc.signed_on = now_datetime()
	doc.status = "Signed by Registrar"
	attach_letter_pdf(doc)
	_save(doc, _("Signed"))
	return get_offer(name)


@frappe.whitelist(methods=["POST"])
def save_signature(signature):
	"""Store a signature image once in Pathways Settings so later orders can
	be signed with one click. Only signatories may set it."""
	if not can_sign():
		frappe.throw(_("Only the Offer Signatory Roles can save a signature."), frappe.PermissionError)
	_check_signature(signature)
	header, encoded = signature.split(",", 1)
	ext = (mimetypes.guess_extension(header[5:].split(";")[0]) or ".png").lstrip(".")
	file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"registrar-signature.{ext}",
			"content": base64.b64decode(encoded),
			"is_private": 1,
			"attached_to_doctype": "Pathways Settings",
			"attached_to_name": "Pathways Settings",
			"attached_to_field": "registrar_signature_image",
		}
	)
	file.flags.ignore_permissions = True
	file.insert()
	frappe.db.set_single_value("Pathways Settings", "registrar_signature_image", file.file_url)
	frappe.clear_document_cache("Pathways Settings", "Pathways Settings")
	return file.file_url


@frappe.whitelist(methods=["POST"])
def send_offer(name, acceptance_deadline=None):
	"""Send the signed order to the candidate (workflow step 28): the letter
	is regenerated with today's date and attached to the appointment_order
	email; the candidate can then respond from the portal."""
	doc = _get(name, "write")
	if doc.status != "Signed by Registrar":
		frappe.throw(_("Only a signed appointment order can be sent (status: {0}).").format(doc.status))
	doc.offer_date = today()
	if acceptance_deadline:
		if getdate(acceptance_deadline) < getdate(today()):
			frappe.throw(_("The acceptance deadline cannot be in the past."))
		doc.acceptance_deadline = acceptance_deadline
	else:
		days = cint(frappe.get_cached_doc("Pathways Settings").acceptance_deadline_days) or 7
		doc.acceptance_deadline = add_days(today(), days)
	doc.status = "Sent"
	doc.sent_by = frappe.session.user
	doc.sent_on = now_datetime()
	attach_letter_pdf(doc)
	_save(doc, _("Sent to candidate"))

	context, candidate = candidate_email_context(doc.application)
	context.update(
		{
			"acceptance_deadline": _fmt_date(doc.acceptance_deadline),
			"designation": doc.designation,
			"pnc_contacts": "",
			"portal_link": get_url(f"/pathways/portal/applications/{doc.application}"),
		}
	)
	send_event("appointment_order", DOCTYPE, doc.name, context, candidate=candidate)
	return get_offer(name)


@frappe.whitelist(methods=["POST"])
def upload_registrar_scan(name, file_url):
	"""Workflow step 29: the scanned copy of the Registrar-signed order."""
	doc = _get(name, "write")
	if doc.status not in CANDIDATE_VISIBLE_STATUSES:
		frappe.throw(_("Upload the scanned signed order once it has been sent."))
	doc.registrar_signed_scan = claim_file(file_url, doc, "registrar_signed_scan")
	doc.save()
	return get_offer(name)


@frappe.whitelist(methods=["POST"])
def delete_offer(name):
	doc = _get(name, "delete")
	if doc.status not in DRAFT_STATUSES:
		frappe.throw(_("Only a draft offer can be deleted."))
	frappe.delete_doc(DOCTYPE, name)
	return True


# ------------------------------------------------------- letter preview


def _check_letter_access(doc):
	if not _is_staff() and doc.status not in CANDIDATE_VISIBLE_STATUSES:
		frappe.throw(_("This letter is not available yet."), frappe.PermissionError)


@frappe.whitelist()
def preview_letter(name):
	doc = _get(name)
	_check_letter_access(doc)
	return render_letter(doc)


@frappe.whitelist()
def download_letter(name):
	"""The PDF: the stored copy once signed (exactly what was signed and
	sent), otherwise generated on the fly as a marked draft."""
	doc = _get(name)
	_check_letter_access(doc)
	content = None
	if doc.letter_pdf and doc.status not in DRAFT_STATUSES and doc.status not in ("Under Review", "Approved for Signature"):
		file_name = frappe.db.get_value("File", {"file_url": doc.letter_pdf}, "name")
		if file_name:
			content = frappe.get_doc("File", file_name).get_content()
	if content is None:
		content = letter_pdf(doc)
	frappe.local.response.filename = f"Appointment Order - {doc.candidate_name or doc.name}.pdf"
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"


# ------------------------------------------------------------ candidate


@frappe.whitelist()
def get_my_offer(application_name):
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")
	candidate_email = frappe.db.get_value("Candidate", app.candidate, "email")
	staff = _is_staff()
	if frappe.session.user != candidate_email and not staff:
		frappe.throw(_("You are not authorised to view this offer."), frappe.PermissionError)

	offer_name = frappe.db.get_value(DOCTYPE, {"application": application_name}, "name")
	if not offer_name:
		return None

	offer = frappe.get_doc(DOCTYPE, offer_name)
	if offer.status not in CANDIDATE_VISIBLE_STATUSES and not staff:
		# Drafts, review and signing are internal.
		return None
	open_for_response = offer.status == "Sent" and (
		not offer.acceptance_deadline or getdate(offer.acceptance_deadline) >= getdate(today())
	)
	return {
		"name": offer.name,
		"status": offer.status,
		"designation": offer.designation,
		"offer_date": offer.offer_date,
		"acceptance_deadline": offer.acceptance_deadline,
		"proposed_doj": offer.proposed_doj,
		"candidate_confirmed_doj": offer.candidate_confirmed_doj,
		"signed_copy_attachment": offer.signed_copy_attachment,
		"responded_on": offer.responded_on,
		"has_letter": offer.status in CANDIDATE_VISIBLE_STATUSES,
		"can_respond": open_for_response,
		"can_upload_signed_copy": offer.status in ("Sent", "Accepted"),
	}


@frappe.whitelist(methods=["POST"])
def respond_to_offer(offer_name, response, confirmed_doj=None, signed_copy_attachment=None, decline_reason=None):
	_get(offer_name)
	return _respond_to_offer(offer_name, response, confirmed_doj, signed_copy_attachment, decline_reason)


@frappe.whitelist(methods=["POST"])
def upload_signed_copy(name, file_url):
	"""The candidate's signed acceptance copy (or staff filing it for them)."""
	doc = _get(name)
	candidate = frappe.db.get_value("Application", doc.application, "candidate")
	candidate_email = frappe.db.get_value("Candidate", candidate, "email") if candidate else None
	if frappe.session.user != candidate_email and not frappe.has_permission(DOCTYPE, "write", doc):
		frappe.throw(_("You cannot upload a signed copy for this offer."), frappe.PermissionError)
	if doc.status not in ("Sent", "Accepted"):
		frappe.throw(_("A signed copy can only be uploaded for an open or accepted offer."))
	doc.signed_copy_attachment = claim_file(file_url, doc, "signed_copy_attachment")
	doc.flags.ignore_permissions = True
	doc.save()
	return doc.signed_copy_attachment
