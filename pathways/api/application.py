# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import now_datetime, today, validate_email_address

from pathways.permissions import CANDIDATE_ROLE, has_full_access
from pathways.utils.application_form import (
	default_upload_rule,
	get_form_config,
	get_required_documents,
	is_accepting_applications,
	name_uploads_for_application,
	sign_upload,
	validate_submission,
)

PUBLIC_JOB_FIELDS = (
	"name",
	"job_title",
	"track",
	"department",
	"designation",
	"vacancies",
	"employment_type",
	"tenure_description",
	"pay_level",
	"application_deadline",
)


@frappe.whitelist(allow_guest=True)
def get_open_job_openings(track=None, department=None, search=None):
	"""Public job board: Advertised jobs whose deadline has not passed."""
	filters = [["status", "=", "Advertised"]]
	if track:
		filters.append(["track", "=", track])
	if department:
		filters.append(["department", "=", department])
	if search:
		filters.append(["job_title", "like", f"%{search}%"])

	jobs = frappe.get_all("Job Opening", filters=filters, fields=list(PUBLIC_JOB_FIELDS), order_by="creation desc")
	now = now_datetime()
	return [j for j in jobs if not j.application_deadline or frappe.utils.get_datetime(j.application_deadline) > now]


def _get_public_job(job_opening):
	if not frappe.db.exists("Job Opening", job_opening):
		frappe.throw(_("This position does not exist."), frappe.DoesNotExistError)
	job = frappe.get_doc("Job Opening", job_opening)
	if job.status != "Advertised":
		frappe.throw(_("This position is not currently open for applications."), frappe.DoesNotExistError)
	return job


def _current_candidate():
	user = frappe.session.user
	if user == "Guest":
		return None
	return frappe.db.get_value(
		"Candidate",
		{"email": user},
		["name", "full_name", "mobile_number", "date_of_birth", "gender", "address"],
		as_dict=True,
	)


@frappe.whitelist(allow_guest=True)
def get_job_opening_detail(job_opening):
	"""Public job detail plus the application form this job asks for."""
	job = _get_public_job(job_opening)
	detail = {field: job.get(field) for field in PUBLIC_JOB_FIELDS}
	detail.update({"jd_text": job.jd_text, "jd_attachment": job.jd_attachment})
	detail["form"] = get_form_config(job)
	# Official notification and corrigenda, published with the posting.
	from pathways.api.job_notice import notice_for

	notice = notice_for(job.name)
	detail["notice"] = {
		"notification": notice["notification"],
		"corrigenda": [
			{k: c.get(k) for k in ("corrigendum_date", "changed_field", "new_value", "remarks", "corrigendum_attachment")}
			for c in notice["corrigenda"]
		],
	}

	user = frappe.session.user
	detail["viewer"] = {"logged_in": user != "Guest", "email": None, "is_staff": False, "already_applied": None}
	if user != "Guest":
		candidate = _current_candidate()
		detail["viewer"].update(
			{
				"email": user,
				"is_staff": frappe.db.get_value("User", user, "user_type") == "System User",
				"profile": candidate,
				"already_applied": candidate
				and frappe.db.get_value(
					"Application",
					{"candidate": candidate.name, "job_opening": job.name, "status": ["!=", "Withdrawn"]},
					"application_id",
				),
			}
		)
	return detail


@frappe.whitelist(allow_guest=True, methods=["POST"])
# A full application is ~15 uploads plus replacements, and applicants on a
# campus network may share one IP.
@rate_limit(limit=120, seconds=10 * 60)
def upload_application_file(job_opening):
	"""Upload one file for an application — the apply form's uploader, so
	guests can apply without an account (Frappe's upload_file refuses
	guests site-wide). Saved private and unattached; the returned token is
	what lets the uploader, and only them, use it in submit_application.
	Format and size are checked per field again on submit."""
	job = _get_public_job(job_opening)
	if not is_accepting_applications(job):
		frappe.throw(_("Applications for this position are closed."))

	upload = frappe.request.files.get("file") if frappe.request else None
	if not upload or not upload.filename:
		frappe.throw(_("No file was uploaded."))
	content = upload.stream.read()

	rules = [default_upload_rule(), *get_required_documents(job)]
	formats = {f for r in rules for f in r["formats"]}
	max_mb = max(r["max_size_mb"] for r in rules)
	extension = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
	if extension not in formats:
		frappe.throw(_("Allowed formats: {0}").format(", ".join(sorted(f.upper() for f in formats))))
	if len(content) > max_mb * 1024 * 1024:
		frappe.throw(_("File is larger than {0} MB.").format(max_mb))

	file = frappe.get_doc(
		{"doctype": "File", "file_name": upload.filename, "is_private": 1, "content": content, "folder": "Home"}
	).insert(ignore_permissions=True)
	return {"file_url": file.file_url, "file_name": file.file_name, "upload_token": sign_upload(file.name)}


@frappe.whitelist(allow_guest=True, methods=["POST"])
# Every attempt counts, including ones rejected by validation, and the apply
# page validates before sending; a campus network may share one IP.
@rate_limit(limit=30, seconds=10 * 60)
def submit_application(job_opening, data):
	"""Submit an application, as a guest or a logged-in candidate.

	Logged in: the candidate is the session user, never an email typed into
	the form. Guest: the candidate is the typed email (matched on email
	only), an existing candidate's profile is never changed by a guest, and
	the acknowledgement goes to that address so its owner sees any
	application made in their name. Either way it is one application per
	email per position, under a row lock.
	"""
	user = frappe.session.user
	if isinstance(data, str):
		data = frappe.parse_json(data)

	if user == "Guest":
		email = ((data.get("candidate") or {}).get("email") or "").strip().lower()
		if not email or not validate_email_address(email):
			_email_error(_("Enter a valid email address."))
		if frappe.db.exists("User", {"email": email, "user_type": "System User"}):
			_email_error(_("Staff email addresses cannot be used to apply. Please use your personal email address."))
	else:
		if frappe.db.get_value("User", user, "user_type") != "Website User":
			frappe.throw(_("Staff accounts cannot apply. Please register with a personal email address."))
		email = user

	# Lock the job row: serialises concurrent submissions for this job and
	# makes the deadline/status check authoritative.
	if not frappe.db.exists("Job Opening", job_opening):
		frappe.throw(_("This position does not exist."))
	frappe.db.get_value("Job Opening", job_opening, "name", for_update=True)
	job = frappe.get_doc("Job Opening", job_opening)
	if not is_accepting_applications(job):
		frappe.throw(_("Applications for this position are closed."))

	candidate_name = frappe.db.get_value("Candidate", {"email": email}, "name", for_update=True)
	if candidate_name and frappe.db.exists(
		"Application", {"candidate": candidate_name, "job_opening": job.name, "status": ["!=", "Withdrawn"]}
	):
		_email_error(
			_("An application from this email address for this position already exists. An application can be submitted only once.")
		)

	candidate_fields, application_fields, files = validate_submission(job, data, user, email=email)

	if candidate_name:
		candidate = frappe.get_doc("Candidate", candidate_name)
		if user != "Guest":
			candidate.update(candidate_fields)
			candidate.save(ignore_permissions=True)
	else:
		candidate = frappe.new_doc("Candidate")
		candidate.update(candidate_fields)
		candidate.email = email
		candidate.insert(ignore_permissions=True)

	application = frappe.new_doc("Application")
	application.update(application_fields)
	application.candidate = candidate.name
	application.application_date = today()
	application.status = "Submitted"
	# The ID is needed up front: stored files are named after it.
	application.set_application_id()
	name_uploads_for_application(application, files)
	application.insert(ignore_permissions=True)

	# Attach the uploads to the application: staff with access to it can
	# then open these private files; nobody else can.
	for file_name in {name for name, _label in files}:
		frappe.db.set_value(
			"File",
			file_name,
			{"attached_to_doctype": "Application", "attached_to_name": application.name},
			update_modified=False,
		)

	if user != "Guest" and not frappe.db.exists("Has Role", {"parenttype": "User", "parent": user, "role": CANDIDATE_ROLE}):
		user_doc = frappe.get_doc("User", user)
		# roles is a permlevel-1 field: without this flag Frappe silently
		# discards role changes a user makes to their own record.
		user_doc.flags.ignore_permissions = True
		user_doc.add_roles(CANDIDATE_ROLE)

	frappe.enqueue(
		"pathways.api.application.send_acknowledgement",
		application_name=application.name,
		enqueue_after_commit=True,
	)
	return {"application_id": application.application_id, "application_name": application.name, "email": email}


def _email_error(message):
	# Shown under the Email field on the apply page.
	frappe.local.response["field_errors"] = {"candidate.email": message}
	frappe.throw(message)


def send_acknowledgement(application_name):
	from pathways.utils.communication import send_templated_email

	if not frappe.db.exists("Email Template", "Application Acknowledgement"):
		return
	app = frappe.get_doc("Application", application_name)
	candidate = frappe.db.get_value("Candidate", app.candidate, ["full_name", "email"], as_dict=True)
	send_templated_email(
		"Application Acknowledgement",
		candidate.email,
		"Application",
		app.name,
		{
			"candidate_name": candidate.full_name,
			"job_title": frappe.db.get_value("Job Opening", app.job_opening, "job_title"),
			"application_id": app.application_id,
		},
	)


@frappe.whitelist()
def get_my_applications():
	"""Applications belonging to the current logged-in candidate —
	server-side scoped via the Candidate's email == session user.
	"""
	candidate = frappe.db.get_value("Candidate", {"email": frappe.session.user}, "name")
	if not candidate:
		return []

	return frappe.get_all(
		"Application",
		filters={"candidate": candidate},
		fields=["name", "application_id", "job_opening", "status", "application_date"],
		order_by="creation desc",
	)


@frappe.whitelist()
def get_application_status(application_name):
	"""Candidate-facing status view — deliberately excludes internal
	notes, interviewer feedback, compensation and other confidential
	data per brief §25/§42.

	frappe.get_doc() does not auto-check permissions on read (unlike
	doc.save() for writes) — the explicit check_permission call below is
	what actually enforces that only the owning candidate or privileged
	staff (has_application_permission, wired via hooks.py) can reach
	this; this function further trims the response shape on top of that.
	"""
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")

	job = frappe.db.get_value(
		"Job Opening", app.job_opening, ["job_title", "department", "track"], as_dict=True
	)

	interviews = frappe.get_all(
		"Interview",
		filters={"application": application_name},
		fields=["round_type", "status", "scheduled_datetime", "mode", "meeting_link", "rsvp_status"],
		order_by="scheduled_datetime asc",
	)

	offer = frappe.db.get_value(
		"Offer Appointment Order",
		{"application": application_name},
		["status", "acceptance_deadline", "candidate_confirmed_doj"],
		as_dict=True,
	)

	doc_collection = frappe.db.get_value(
		"Document Collection", {"application": application_name}, "overall_status"
	)

	return {
		"application_id": app.application_id,
		"status": app.status,
		"job_title": job.job_title if job else None,
		"department": job.department if job else None,
		"application_date": app.application_date,
		"interviews": interviews,
		"offer_status": offer.status if offer else None,
		"acceptance_deadline": offer.acceptance_deadline if offer else None,
		"document_status": doc_collection,
	}


@frappe.whitelist()
def delete_application(application):
	"""Deletes an Application. delete_doc enforces delete permission on
	its own — only Pathways Admin/System Manager hold delete on this
	doctype (see application.json); Recruiter naturally gets a
	PermissionError here without any extra check.
	"""
	frappe.delete_doc("Application", application)
	return {"deleted": application}


FINAL_STATUSES = ("Withdrawn", "Not Selected", "Joined", "Offer Accepted")


@frappe.whitelist(methods=["POST"])
def withdraw_application(application_name):
	"""The candidate, or staff who may edit every Application, can withdraw."""
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")
	candidate_email = frappe.db.get_value("Candidate", app.candidate, "email")
	is_owner = frappe.session.user == candidate_email
	if not is_owner and not (has_full_access("Application") and frappe.has_permission("Application", "write")):
		frappe.throw(_("You are not authorised to withdraw this application."), frappe.PermissionError)
	if app.status in FINAL_STATUSES:
		frappe.throw(_("An application that is {0} cannot be withdrawn.").format(_(app.status)))

	app.status = "Withdrawn"
	app.save(ignore_permissions=True)
	return app.status


# Statuses normally set by their own records (Offer / Appointment Order,
# Document Collection, Joining) or by the candidate (Withdrawn). Staff may
# move an application through screening and selection by hand; these need
# Pathways Settings > Job Status Override Role (or System Manager).
SYSTEM_DRIVEN_STATUSES = (
	"Offer Extended",
	"Offer Accepted",
	"Offer Declined",
	"Documents Pending",
	"Documents Verified",
	"Joined",
	"Withdrawn",
)


def _settable_statuses(app):
	from pathways.pathways.doctype.job_opening.job_opening import can_override_status

	options = frappe.get_meta("Application").get_field("status").options.split("\n")
	if can_override_status():
		return options
	return [s for s in options if s not in SYSTEM_DRIVEN_STATUSES or s == app.status]


def _get_staff_application(application_name, ptype):
	app = frappe.get_doc("Application", application_name)
	app.check_permission(ptype)
	if frappe.db.get_value("User", frappe.session.user, "user_type") != "System User":
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	return app


@frappe.whitelist()
def get_application_status_options(application_name):
	"""What the Change Status dialog may offer this user."""
	app = _get_staff_application(application_name, "read")
	if not frappe.has_permission("Application", "write", doc=app):
		return {"can_change": False}
	return {"can_change": True, "current": app.status, "options": _settable_statuses(app)}


@frappe.whitelist(methods=["POST"])
def set_application_status(application_name, status, remarks=None):
	"""Change an application's status by hand. The change and any remarks
	are recorded in the application's timeline."""
	app = _get_staff_application(application_name, "write")
	if status not in _settable_statuses(app):
		frappe.throw(_("You cannot set the status to {0}. It is set from its own record.").format(status))
	if status == app.status:
		return app.status

	previous = app.status
	app.status = status
	app.save()
	remarks = (remarks or "").strip()
	note = _("Status changed from {0} to {1}.").format(previous, status)
	app.add_comment("Info", note + (f" {_('Remarks')}: {frappe.utils.escape_html(remarks)}" if remarks else ""))
	return app.status


# ------------------------------------------------------------ documents


def _application_documents(app):
	"""Every uploaded file on the application, in reading order:
	[{label, group, file_url, file_name, kind}]."""
	rows = [("Resume / CV", "Application", app.resume_attachment), ("Statement of Purpose", "Application", app.sop_attachment)]
	for q in app.qualifications or []:
		level = {"Undergraduate": "Graduate Degree", "Postgraduate": "Post Graduate Degree", "Doctoral": "Doctoral Degree"}.get(q.degree_level, q.degree_level)
		rows.append((f"{level} — Transcript", "Qualifications", q.transcript_attachment))
		rows.append((f"{level} — Degree Certificate", "Qualifications", q.certificate_attachment))
	for i, pub in enumerate(app.get("publications") or [], start=1):
		rows.append((f"Publication #{i}", "Publications", pub.pdf_attachment))
	for d in app.documents or []:
		rows.append((d.document_type, "Supporting Documents", d.attachment))
	rows.append(("Additional Documents", "Supporting Documents", app.additional_attachment))

	out = []
	for label, group, url in rows:
		if not url:
			continue
		extension = url.rsplit(".", 1)[-1].lower() if "." in url else ""
		kind = "pdf" if extension == "pdf" else "image" if extension in ("jpg", "jpeg", "png", "gif", "webp") else "other"
		out.append({"label": label, "group": group, "file_url": url, "file_name": url.rsplit("/", 1)[-1], "kind": kind})
	return out


@frappe.whitelist()
def list_application_documents():
	"""Documents page: every application the user may read, with the
	candidate, the job and how many files were uploaded."""
	if frappe.db.get_value("User", frappe.session.user, "user_type") != "System User":
		frappe.throw(_("Not permitted."), frappe.PermissionError)

	apps = frappe.get_list(
		"Application",
		fields=[
			"name",
			"application_id",
			"candidate",
			"job_opening",
			"status",
			"application_date",
			"resume_attachment",
			"sop_attachment",
			"additional_attachment",
		],
		order_by="creation desc",
		limit_page_length=0,
	)
	if not apps:
		return []
	names = [a.name for a in apps]

	candidates = {
		c.name: c
		for c in frappe.get_all(
			"Candidate",
			filters={"name": ["in", list({a.candidate for a in apps})]},
			fields=["name", "full_name", "email"],
		)
	}
	jobs = dict(
		frappe.get_all(
			"Job Opening", filters={"name": ["in", list({a.job_opening for a in apps})]}, fields=["name", "job_title"], as_list=True
		)
	)
	# Count uploaded slots (what the document viewer lists), not File rows:
	# one stored file may fill several slots.
	counts = {a.name: sum(1 for f in ("resume_attachment", "sop_attachment", "additional_attachment") if a.get(f)) for a in apps}
	for parent, n in frappe.db.sql(
		"""
		select parent, sum((ifnull(transcript_attachment, '') != '') + (ifnull(certificate_attachment, '') != ''))
		from `tabApplication Qualification` where parenttype = 'Application' and parent in %(names)s group by parent
		""",
		{"names": names},
	):
		counts[parent] += int(n or 0)
	for parent, n in frappe.db.sql(
		"""
		select parent, count(*) from `tabApplication Document`
		where parenttype = 'Application' and parent in %(names)s and ifnull(attachment, '') != '' group by parent
		""",
		{"names": names},
	):
		counts[parent] += int(n or 0)
	for a in apps:
		candidate = candidates.get(a.candidate) or {}
		a.candidate_name = candidate.get("full_name")
		a.candidate_email = candidate.get("email")
		a.job_title = jobs.get(a.job_opening) or a.job_opening
		a.document_count = counts[a.name]
		for f in ("resume_attachment", "sop_attachment", "additional_attachment"):
			a.pop(f, None)
	return apps


@frappe.whitelist()
def get_application_documents(application_name):
	"""Documents for the staff document viewer."""
	app = _get_staff_application(application_name, "read")
	return {"application_id": app.application_id, "documents": _application_documents(app)}


@frappe.whitelist()
def download_application_documents(application_name):
	"""All of the application's documents as one PDF, a bookmark per
	document. Images become pages; a file that cannot be merged (e.g. a
	Word document) gets a page saying to download it separately."""
	import io

	from PIL import Image, ImageDraw
	from pypdf import PdfReader, PdfWriter

	app = _get_staff_application(application_name, "read")
	writer = PdfWriter()

	def note_page(text):
		page = Image.new("RGB", (1240, 1754), "white")  # A4 at 150 dpi
		ImageDraw.Draw(page).multiline_text((100, 120), text, fill="black", spacing=12)
		buffer = io.BytesIO()
		page.save(buffer, "PDF", resolution=150)
		return PdfReader(io.BytesIO(buffer.getvalue()))

	for doc in _application_documents(app):
		start = len(writer.pages)
		try:
			file = frappe.get_doc("File", {"file_url": doc["file_url"], "attached_to_name": app.name})
			content = file.get_content()
			if doc["kind"] == "pdf":
				reader = PdfReader(io.BytesIO(content))
			elif doc["kind"] == "image":
				image = Image.open(io.BytesIO(content))
				image = image.convert("RGB")
				buffer = io.BytesIO()
				image.save(buffer, "PDF", resolution=150)
				reader = PdfReader(io.BytesIO(buffer.getvalue()))
			else:
				reader = note_page(f"{doc['label']}\n\n{doc['file_name']}\n\nThis file type cannot be shown here.\nDownload it separately from the application.")
		except Exception:
			frappe.log_error(f"Could not merge {doc['file_url']} for {app.name}", "Application documents")
			reader = note_page(f"{doc['label']}\n\n{doc['file_name']}\n\nThis file could not be read.\nDownload it separately from the application.")
		for page in reader.pages:
			writer.add_page(page)
		if len(writer.pages) > start:
			writer.add_outline_item(doc["label"], start)

	if not writer.pages:
		frappe.throw(_("This application has no documents."))

	buffer = io.BytesIO()
	writer.write(buffer)
	frappe.local.response.filename = f"{app.application_id}_All-Documents.pdf"
	frappe.local.response.filecontent = buffer.getvalue()
	frappe.local.response.type = "download"


@frappe.whitelist()
def get_application_detail(application_name):
	"""Full submitted application for staff (and assigned committee members)."""
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")
	if frappe.db.get_value("User", frappe.session.user, "user_type") != "System User":
		frappe.throw(_("Not permitted."), frappe.PermissionError)

	# Every Candidate field the page shows (candidate_fields below), not a fixed list.
	candidate_fields = _data_fields("Candidate")
	candidate = frappe.db.get_value("Candidate", app.candidate, [df.fieldname for df in candidate_fields], as_dict=True)
	out = app.as_dict(no_default_fields=True)
	out["candidate_details"] = candidate
	out["job_title"] = frappe.db.get_value("Job Opening", app.job_opening, "job_title")
	out["can_write"] = bool(frappe.has_permission("Application", "write", doc=app))
	out["can_delete"] = bool(frappe.has_permission("Application", "delete", doc=app))
	if not has_full_access("Application"):
		# Committee members review merit, not pay.
		for field in ("current_salary", "expected_salary"):
			out.pop(field, None)
	# The same person's applications to other openings (one Candidate per
	# email). get_list, not get_all: a committee member sees only the
	# applications their permissions allow.
	others = frappe.get_list(
		"Application",
		filters={"candidate": app.candidate, "name": ["!=", app.name]},
		fields=["name", "application_id", "job_opening", "status", "application_date"],
		order_by="creation desc",
	)
	titles = dict(
		frappe.get_all(
			"Job Opening",
			filters={"name": ["in", [o.job_opening for o in others]]},
			fields=["name", "job_title"],
			as_list=True,
		)
	) if others else {}
	for other in others:
		other["job_title"] = titles.get(other.job_opening)
	out["other_applications"] = others
	out["activity"] = _application_activity(app)

	out["layout"] = form_layout("Application", visible=set(out))
	out["candidate_fields"] = [_field_def(df) for df in candidate_fields]
	return out


def _application_activity(app):
	"""Newest-first timeline: status changes and the notes recorded on the
	application (e.g. shortlisting decisions, manual status remarks)."""
	events = [
		{
			"kind": "status",
			"at": h.changed_on,
			"by": frappe.utils.get_fullname(h.changed_by),
			"from_status": h.previous_status,
			"to_status": h.new_status,
		}
		for h in frappe.get_all(
			"Application Status History",
			filters={"application": app.name},
			fields=["previous_status", "new_status", "changed_by", "changed_on"],
		)
	]
	events += [
		{
			"kind": "note",
			"at": c.creation,
			"by": frappe.utils.get_fullname(c.owner),
			"text": frappe.utils.strip_html(c.content or ""),
		}
		for c in frappe.get_all(
			"Comment",
			filters={"reference_doctype": "Application", "reference_name": app.name, "comment_type": ["in", ["Info", "Comment"]]},
			fields=["content", "owner", "creation"],
		)
	]
	events.append({"kind": "created", "at": app.creation, "by": frappe.utils.get_fullname(app.owner)})

	# A note written with a status change (same save) describes it: show it
	# on that change instead of as a second entry.
	changes = [e for e in events if e["kind"] == "status"]
	merged = []
	for event in events:
		if event["kind"] == "note":
			at = frappe.utils.get_datetime(event["at"])
			match = next(
				(c for c in changes if "note" not in c and abs((frappe.utils.get_datetime(c["at"]) - at).total_seconds()) < 5),
				None,
			)
			if match:
				match["note"] = event["text"]
				continue
		merged.append(event)
	return sorted(merged, key=lambda e: e["at"], reverse=True)


LAYOUT_SKIP = {"naming_series", "candidate"}  # candidate: shown as its own fields


def _data_fields(doctype):
	from frappe.model import no_value_fields

	return [
		df
		for df in frappe.get_meta(doctype).fields
		if df.fieldtype not in no_value_fields and not df.hidden and df.fieldname not in LAYOUT_SKIP
	]


def _field_def(df):
	field = {"fieldname": df.fieldname, "label": _(df.label or df.fieldname), "fieldtype": df.fieldtype}
	if df.fieldtype == "Table":
		field["columns"] = [_field_def(child) for child in _data_fields(df.options)]
	return field


def form_layout(doctype, visible=None):
	"""The DocType's own form layout — tabs > sections > columns > fields —
	so the Vue page shows every field, filled or not, in the same places as
	Desk. Fields not in `visible` (removed for this user) are left out."""
	tabs = [{"key": "details", "label": _("Details"), "sections": []}]
	section = None

	def new_section(label=None):
		nonlocal section
		section = {"label": _(label) if label else None, "columns": [[]]}
		tabs[-1]["sections"].append(section)

	new_section()
	for df in frappe.get_meta(doctype).fields:
		if df.hidden or df.fieldname in LAYOUT_SKIP:
			continue
		if df.fieldtype == "Tab Break":
			tabs.append({"key": df.fieldname, "label": _(df.label or df.fieldname), "sections": []})
			new_section()
		elif df.fieldtype == "Section Break":
			new_section(df.label)
		elif df.fieldtype == "Column Break":
			section["columns"].append([])
		elif visible is None or df.fieldname in visible:
			from frappe.model import no_value_fields

			if df.fieldtype == "Table" or df.fieldtype not in no_value_fields:
				section["columns"][-1].append(_field_def(df))

	for tab in tabs:
		for sec in tab["sections"]:
			sec["columns"] = [col for col in sec["columns"] if col]
		tab["sections"] = [sec for sec in tab["sections"] if sec["columns"]]
	return [tab for tab in tabs if tab["sections"]]


@frappe.whitelist(methods=["POST"])
def bulk_set_application_status(names, status, remarks=None):
	"""Change Status for several applications (list page bulk action)."""
	from pathways.utils.bulk import run_bulk

	return run_bulk(names, lambda name: set_application_status(name, status, remarks))


@frappe.whitelist(methods=["POST"])
def bulk_delete_applications(names):
	from pathways.utils.bulk import run_bulk

	return run_bulk(names, lambda name: frappe.delete_doc("Application", name))


# ------------------------------------------------------------ documents ZIP
# Workflow step 10: everyone's CVs, SOPs, writing samples... in one folder
# per document type, for the shortlisting committee.

ZIP_SCOPES = {
	"all": None,
	"eligible": {"eligibility_status": "Eligible"},
	"shortlisted": {"status": ["in", ["Shortlisted", "Interview Scheduled", "Interview Completed", "Selected"]]},
}


def _zip_folder(label):
	"""Folder for a document label from _application_documents."""
	if label == "Resume / CV":
		return "CV", ""
	if label == "Statement of Purpose":
		return "SOP", ""
	if label.endswith("— Transcript"):
		return "Transcripts", label.split(" — ")[0]
	if label.endswith("— Degree Certificate"):
		return "Degree Certificates", label.split(" — ")[0]
	if label.startswith("Publication #"):
		return "Publications", label.split("#")[1]
	return re.sub(r'[\\/:*?"<>|]+', "-", label).strip(" -") or "Other", ""


@frappe.whitelist()
def download_documents_zip(job_opening=None, applications=None, scope="all"):
	"""ZIP of applicants' documents, one folder per document type. Either a
	job (scope: all / eligible / shortlisted) or a list of applications."""
	import io
	import zipfile

	from pathways.api.scoring import can_shortlist

	if applications:
		names = frappe.parse_json(applications) if isinstance(applications, str) else applications
		label = "selected-applications"
	elif job_opening:
		if not can_shortlist(job_opening):
			frappe.throw(_("Only the recruitment team or this job's committee can download its documents."), frappe.PermissionError)
		if scope not in ZIP_SCOPES:
			frappe.throw(_("Unknown selection."))
		names = frappe.get_all(
			"Application",
			filters={"job_opening": job_opening, "status": ["!=", "Withdrawn"], **(ZIP_SCOPES[scope] or {})},
			pluck="name",
			order_by="application_id asc",
			ignore_permissions=True,
		)
		label = f"{frappe.db.get_value('Job Opening', job_opening, 'position') or job_opening}_{scope}"
	else:
		frappe.throw(_("Choose a job or applications."))
	if not names:
		frappe.throw(_("There are no applications to download."))

	buffer = io.BytesIO()
	count = 0
	with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
		for name in names:
			app = frappe.get_doc("Application", name)
			if not job_opening:
				app.check_permission("read")
			person = re.sub(r"[^\w .-]+", "", frappe.db.get_value("Candidate", app.candidate, "full_name") or "").strip()
			for doc in _application_documents(app):
				folder, part = _zip_folder(doc["label"])
				extension = doc["file_name"].rsplit(".", 1)[-1] if "." in doc["file_name"] else "bin"
				filename = f"{app.application_id} - {person}{f' - {part}' if part else ''}.{extension}"
				try:
					file = frappe.get_doc("File", {"file_url": doc["file_url"], "attached_to_name": app.name})
					archive.writestr(f"{folder}/{filename}", file.get_content())
					count += 1
				except Exception:
					frappe.log_error(f"Could not add {doc['file_url']} for {app.name}", "Documents ZIP")
	if not count:
		frappe.throw(_("These applications have no documents."))

	frappe.local.response.filename = f"{label}_documents.zip"
	frappe.local.response.filecontent = buffer.getvalue()
	frappe.local.response.type = "download"


@frappe.whitelist(methods=["POST"])
def export_applications(names, mode="single"):
	"""Applications list > Export: the full applications as an Excel
	workbook, one sheet for all (mode=single) or a sheet per job opening
	(mode=job_wise)."""
	from pathways.utils.application_export import build_workbook

	if frappe.db.get_value("User", frappe.session.user, "user_type") != "System User":
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	content, _count = build_workbook(names, mode)
	suffix = "job-wise" if mode == "job_wise" else "all"
	frappe.local.response.filename = f"applications-{suffix}-{today()}.xlsx"
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"
