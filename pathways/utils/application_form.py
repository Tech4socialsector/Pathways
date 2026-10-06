# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""The candidate application form: what a Job Opening asks for, and the
server-side validation of a submission against it.

The form a candidate sees (get_form_config) and the checks run on submit
(validate_submission) are built from the same Job Opening configuration,
so the two can never disagree. Frontend validation is UX only.

Per-job configuration (Job Opening > Application Form):
	application_deadline   applications close at this moment (site timezone)
	require_postgraduate   PG degree section becomes mandatory
	screening_questions    e.g. "Do you have 15 years of ... experience?"
	required_documents     supporting uploads; defaults to Document Type Master
"""

import hashlib
import hmac
import os
import re
import shutil

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate, now_datetime, today, validate_email_address

YES_NO = ("Yes", "No")


# ------------------------------------------------------------ guest uploads


def sign_upload(file_name):
	"""Token proving the bearer uploaded this File: "<File name>.<signature>".
	Guests share the owner "Guest", and identical content shares one
	file_url, so neither can tell one applicant's upload from another's;
	the token names the exact File and is returned only to its uploader."""
	return f"{file_name}.{_upload_signature(file_name)}"


def _upload_signature(file_name):
	from frappe.utils.password import get_encryption_key

	key = get_encryption_key().encode()
	return hmac.new(key, f"application-upload:{file_name}".encode(), hashlib.sha256).hexdigest()


def get_guest_upload(token, file_url):
	"""File name the token proves, if it is a Guest upload of file_url."""
	file_name, _, signature = str(token or "").partition(".")
	if not (file_name and signature and hmac.compare_digest(_upload_signature(file_name), signature)):
		return None
	return frappe.db.get_value("File", {"name": file_name, "file_url": file_url, "owner": "Guest"}, "name")


# ------------------------------------------------------------ configuration


def _settings():
	return frappe.get_cached_doc("Pathways Settings")


def _formats(text):
	return [f.strip().lower().lstrip(".") for f in (text or "").split(",") if f.strip()]


def default_upload_rule():
	settings = _settings()
	return {
		"max_size_mb": flt(settings.get("application_max_file_size_mb")) or 5,
		"formats": _formats(settings.get("application_allowed_formats")) or ["pdf", "jpg", "jpeg", "png"],
	}


def get_required_documents(job):
	"""[{document_type, label, mandatory, max_size_mb, formats}] for this job."""
	rows = []
	if job.get("required_documents"):
		for row in job.required_documents:
			master = frappe.db.get_value(
				"Document Type Master",
				row.document_type,
				["name", "max_file_size_mb", "allowed_formats", "is_active"],
				as_dict=True,
			)
			if master and master.is_active:
				rows.append((master, cint(row.is_mandatory)))
	else:
		masters = frappe.get_all(
			"Document Type Master",
			filters={"is_active": 1, "used_in": ["in", ["Application", "Both"]]},
			or_filters=[["track", "is", "not set"], ["track", "=", job.track or ""]],
			fields=["name", "max_file_size_mb", "allowed_formats", "requirement"],
			order_by="creation asc",
		)
		rows = [(m, 1 if m.requirement == "Mandatory" else 0) for m in masters]

	fallback = default_upload_rule()
	return [
		{
			"document_type": master.name,
			"label": master.name,
			"mandatory": mandatory,
			"max_size_mb": flt(master.max_file_size_mb) or fallback["max_size_mb"],
			"formats": _formats(master.allowed_formats) or fallback["formats"],
		}
		for master, mandatory in rows
	]


def is_accepting_applications(job):
	if job.status != "Advertised":
		return False
	return not job.application_deadline or get_datetime(job.application_deadline) > now_datetime()


def get_form_config(job):
	"""Public description of the form for this job (safe for guests)."""
	questions = [
		{
			"idx": q.idx,
			"question": q.question,
			"answer_type": q.answer_type,
			"options": [o.strip() for o in (q.options or "").splitlines() if o.strip()],
			"mandatory": cint(q.is_mandatory),
			"ask_details_if_yes": cint(q.ask_details_if_yes),
			"details_label": q.details_label or _("Please describe the relevant experience in brief."),
		}
		for q in job.get("screening_questions") or []
	]
	return {
		"application_deadline": job.application_deadline,
		"is_open": is_accepting_applications(job),
		"require_postgraduate": cint(job.require_postgraduate),
		"screening_questions": questions,
		"required_documents": get_required_documents(job),
		"upload_rule": default_upload_rule(),
		"sources": frappe.get_all(
			"Candidate Source", filters={"is_active": 1}, pluck="name", order_by="creation asc"
		),
		"declaration": _settings().get("application_declaration") or "",
	}


# --------------------------------------------------------------- validation


class FormErrors:
	"""Collect every problem so the candidate sees them all at once. Each
	message may name the form field it belongs to (e.g. "candidate.email",
	"ref.0.mobile"); the apply page shows it under that field."""

	def __init__(self):
		self.messages = []
		self.fields = {}

	def add(self, message, field=None):
		self.messages.append(message)
		if field and field not in self.fields:
			self.fields[field] = message

	def require(self, value, label, field=None):
		if value is None or (isinstance(value, str) and not value.strip()):
			self.add(_("{0} is required.").format(label), field)
			return False
		return True

	def raise_if_any(self):
		if self.messages:
			frappe.local.response["field_errors"] = self.fields
			frappe.throw(
				"<ul>" + "".join(f"<li>{frappe.utils.escape_html(m)}</li>" for m in self.messages) + "</ul>",
				title=_("Please correct the following"),
			)


def _text(value):
	return (value or "").strip() if isinstance(value, str) else value


def _percentage(value, label, errors, field=None):
	try:
		number = float(str(value).strip().rstrip("%"))
	except (TypeError, ValueError):
		errors.add(_("{0}: enter the percentage as a number (convert CGPA using your university's table).").format(label), field)
		return None
	if not 0 <= number <= 100:
		errors.add(_("{0}: percentage must be between 0 and 100.").format(label), field)
	return number


def _year(value, label, errors, field=None):
	year = cint(value)
	if not 1950 <= year <= getdate(today()).year + 1:
		errors.add(_("{0}: enter a valid year.").format(label), field)
	return year


def _date(value, label, errors, field=None):
	if not value:
		return None
	try:
		return getdate(value)
	except Exception:
		errors.add(_("{0}: invalid date.").format(label), field)
		return None


def _number(value, label, errors, field=None, minimum=0, maximum=None):
	"""A required non-negative number; None if missing or invalid."""
	if value in (None, ""):
		errors.add(_("{0} is required (enter 0 if not applicable).").format(label), field)
		return None
	try:
		number = float(str(value).strip())
	except ValueError:
		errors.add(_("{0}: enter a number.").format(label), field)
		return None
	if number < minimum or (maximum is not None and number > maximum):
		errors.add(_("{0}: enter a valid value.").format(label), field)
		return None
	return number


def mobile_error(value):
	"""Indian mobile (10 digits, starting 6-9) or an international number
	with country code (+, 8-15 digits). Spaces and hyphens are ignored."""
	number = re.sub(r"[\s\-]", "", value or "")
	if number.startswith("+"):
		if not re.fullmatch(r"\+[1-9][0-9]{7,14}", number):
			return _("Enter a valid mobile number with country code, e.g. +44 7911 123456.")
	elif not re.fullmatch(r"[6-9][0-9]{9}", number):
		return _("Enter a valid 10-digit mobile number.")
	return None


def check_file(file_url, user, rule, label, errors, upload_tokens=None):
	"""The upload must exist, belong to this candidate, be private, not be
	attached to anything else yet, and match the size/format rule — so a
	candidate can never point their application at someone else's file.
	A guest proves ownership with the token issued at upload
	(upload_tokens: {file_url: token})."""
	if not file_url:
		return None
	if user == "Guest":
		filters = {"name": get_guest_upload((upload_tokens or {}).get(file_url), file_url)}
	else:
		filters = {"file_url": file_url, "owner": user}
	file = filters.get("name", True) and frappe.db.get_value(
		"File",
		filters,
		["name", "file_size", "is_private", "attached_to_doctype", "attached_to_name"],
		as_dict=True,
	)
	if not file:
		errors.add(_("{0}: the uploaded file was not found. Please upload it again.").format(label))
		return None
	if file.attached_to_doctype:
		errors.add(_("{0}: this file is already used elsewhere. Please upload it again.").format(label))
		return None
	if not file.is_private:
		errors.add(_("{0}: please upload the file again.").format(label))
		return None
	extension = os.path.splitext(file_url)[1].lower().lstrip(".")
	if rule["formats"] and extension not in rule["formats"]:
		errors.add(
			_("{0}: allowed formats are {1}.").format(label, ", ".join(f.upper() for f in rule["formats"]))
		)
	if rule["max_size_mb"] and cint(file.file_size) > rule["max_size_mb"] * 1024 * 1024:
		errors.add(_("{0}: file is larger than {1} MB.").format(label, rule["max_size_mb"]))
	return file.name


def validate_submission(job, data, user, email=None):
	"""Validate a submission against the job's form. Returns
	(candidate_fields, application_fields, files) ready to save, where files
	is [(File name, label)] for the uploads used.
	email is the applicant's address: the login for a logged-in candidate,
	the typed address for a guest (user == "Guest")."""
	errors = FormErrors()
	rule = default_upload_rule()
	files = []
	email = email or user
	upload_tokens = data.get("upload_tokens") or {}

	def upload(url, label, required, field):
		if not url:
			if required:
				errors.add(_("{0} is required.").format(label), field)
			return None
		before = len(errors.messages)
		name = check_file(url, user, rule, label, errors, upload_tokens)
		if len(errors.messages) > before:
			errors.fields.setdefault(field, errors.messages[-1])
		if name:
			files.append((name, label))
		return url

	# --- personal details
	personal = data.get("candidate") or {}
	full_name = _text(personal.get("full_name"))
	mobile = _text(personal.get("mobile_number"))
	if errors.require(full_name, _("Name"), "candidate.full_name") and not re.search(r"[^\W\d_]", full_name):
		errors.add(_("Enter your name."), "candidate.full_name")
	if errors.require(mobile, _("Mobile Number"), "candidate.mobile_number") and mobile_error(mobile):
		errors.add(mobile_error(mobile), "candidate.mobile_number")
	dob = _date(personal.get("date_of_birth"), _("Date of Birth"), errors, "candidate.date_of_birth")
	if not personal.get("date_of_birth"):
		errors.add(_("Date of Birth is required."), "candidate.date_of_birth")
	elif dob and (dob >= getdate(today()) or getdate(today()).year - dob.year > 100):
		errors.add(_("Enter a valid Date of Birth."), "candidate.date_of_birth")
	elif dob and frappe.utils.date_diff(today(), dob) < 18 * 365.25:
		errors.add(_("You must be at least 18 years old to apply."), "candidate.date_of_birth")
	gender = personal.get("gender")
	if gender not in ("Female", "Male", "Prefer not to say", "Other"):
		errors.add(_("Gender is required."), "candidate.gender")
	address = _text(personal.get("address"))
	errors.require(address, _("Address for Correspondence"), "candidate.address")

	# --- qualifications
	app = data.get("application") or {}
	qualifications = []
	for level, label, required in (
		("Undergraduate", _("Graduate Degree"), True),
		("Postgraduate", _("Post Graduate Degree"), bool(cint(job.require_postgraduate))),
	):
		key = f"qual.{level}"
		row = next((q for q in app.get("qualifications") or [] if q.get("degree_level") == level), None)
		filled = row and any(_text(row.get(k)) for k in ("degree_name", "other_institution", "year_of_graduation"))
		if not filled:
			if required:
				errors.add(_("{0} details are required.").format(label), f"{key}.degree_name")
			continue
		errors.require(_text(row.get("degree_name")), _("{0}: Name of the Degree").format(label), f"{key}.degree_name")
		errors.require(_text(row.get("other_institution")), _("{0}: College / University").format(label), f"{key}.other_institution")
		_year(row.get("year_of_graduation"), label, errors, f"{key}.year_of_graduation")
		if dob and cint(row.get("year_of_graduation")) and cint(row.get("year_of_graduation")) < dob.year + 15:
			errors.add(_("{0}: year of graduation does not match your Date of Birth.").format(label), f"{key}.year_of_graduation")
		_percentage(row.get("percentage_or_cgpa"), label, errors, f"{key}.percentage_or_cgpa")
		errors.require(_text(row.get("division_grade")), _("{0}: Division / Grade").format(label), f"{key}.division_grade")
		errors.require(_text(row.get("specialization")), _("{0}: Specialization").format(label), f"{key}.specialization")
		qualifications.append(
			{
				"degree_level": level,
				"degree_name": _text(row.get("degree_name")),
				"other_institution": _text(row.get("other_institution")),
				"year_of_graduation": cint(row.get("year_of_graduation")),
				"percentage_or_cgpa": str(row.get("percentage_or_cgpa") or "").strip(),
				"division_grade": _text(row.get("division_grade")),
				"specialization": _text(row.get("specialization")),
				"transcript_attachment": upload(
					row.get("transcript_attachment"), _("{0}: Transcript").format(label), required, f"{key}.transcript_attachment"
				),
				"certificate_attachment": upload(
					row.get("certificate_attachment"),
					_("{0}: Degree Certificate").format(label),
					required,
					f"{key}.certificate_attachment",
				),
			}
		)

	# --- experience
	overall = _number(app.get("overall_experience_years"), _("Overall work experience"), errors, "application.overall_experience_years", maximum=60)
	relevant = _number(app.get("relevant_experience_years"), _("Relevant work experience"), errors, "application.relevant_experience_years", maximum=60)
	overall, relevant = flt(overall, 1), flt(relevant, 1)
	if relevant > overall:
		errors.add(_("Relevant experience cannot exceed overall experience."), "application.relevant_experience_years")

	employment = []
	for i, row in enumerate(app.get("employment_history") or [], start=1):
		if not any(_text(row.get(k)) for k in ("designation", "employer_name", "from_date")):
			continue
		label = _("Organisation #{0}").format(i)
		key = f"emp.{i - 1}"
		errors.require(_text(row.get("designation")), _("{0}: Designation").format(label), f"{key}.designation")
		errors.require(_text(row.get("employer_name")), _("{0}: Name of the employer").format(label), f"{key}.employer_name")
		start = _date(row.get("from_date"), _("{0}: From Date").format(label), errors, f"{key}.from_date")
		if not row.get("from_date"):
			errors.add(_("{0}: From Date is required.").format(label), f"{key}.from_date")
		is_current = cint(row.get("is_current"))
		end = None if is_current else _date(row.get("to_date"), _("{0}: To Date").format(label), errors, f"{key}.to_date")
		if not is_current and not row.get("to_date"):
			errors.add(_("{0}: To Date is required (or tick 'Currently working here').").format(label), f"{key}.to_date")
		if start and end and end < start:
			errors.add(_("{0}: To Date cannot be before From Date.").format(label), f"{key}.to_date")
		if start and start > getdate(today()):
			errors.add(_("{0}: From Date cannot be in the future.").format(label), f"{key}.from_date")
		if end and end > getdate(today()):
			errors.add(_("{0}: To Date cannot be in the future.").format(label), f"{key}.to_date")
		if i == 1:
			errors.require(_text(row.get("key_responsibilities")), _("{0}: Key Responsibilities").format(label), f"{key}.key_responsibilities")
		employment.append(
			{
				"designation": _text(row.get("designation")),
				"employer_name": _text(row.get("employer_name")),
				"from_date": start,
				"to_date": end,
				"is_current": is_current,
				"key_responsibilities": _text(row.get("key_responsibilities")),
			}
		)
	if overall > 0 and not employment:
		errors.add(_("Add at least your most recent organisation under Professional Experience."), "emp.0.designation")
	notice_period = _text(app.get("notice_period"))
	if employment:
		errors.require(notice_period, _("Current Notice Period"), "application.notice_period")

	# --- screening questions
	answers_in = {cint(a.get("idx")): a for a in app.get("screening_answers") or []}
	screening = []
	for q in job.get("screening_questions") or []:
		key = f"screening.{q.idx}"
		given = answers_in.get(q.idx) or {}
		answer = _text(str(given.get("answer") if given.get("answer") is not None else ""))
		details = _text(given.get("details"))
		if not answer:
			if cint(q.is_mandatory):
				errors.add(_("Please answer: {0}").format(q.question), key)
			screening.append({"question": q.question, "answer_type": q.answer_type, "answer": "", "details": ""})
			continue
		if q.answer_type == "Yes/No" and answer not in YES_NO:
			errors.add(_("Answer Yes or No: {0}").format(q.question), key)
		elif q.answer_type == "Single Choice":
			options = [o.strip() for o in (q.options or "").splitlines() if o.strip()]
			if answer not in options:
				errors.add(_("Choose one of the listed options: {0}").format(q.question), key)
		elif q.answer_type == "Number":
			try:
				float(answer)
			except ValueError:
				errors.add(_("Enter a number: {0}").format(q.question), key)
		if q.answer_type == "Yes/No" and cint(q.ask_details_if_yes) and answer == "Yes" and not details:
			errors.add(_("Please add details for: {0}").format(q.question), f"{key}.details")
		screening.append(
			{
				"question": q.question,
				"answer_type": q.answer_type,
				"answer": answer,
				"details": details if answer == "Yes" or q.answer_type != "Yes/No" else "",
			}
		)

	# --- references (two supervisors)
	references = []
	for i, row in enumerate((app.get("references") or [])[:2], start=1):
		label = _("Referee #{0}").format(i)
		key = f"ref.{i - 1}"
		values = {
			"referee_name": _text(row.get("referee_name")),
			"current_designation_org": _text(row.get("current_designation_org")),
			"relationship": _text(row.get("relationship")),
			"email": (_text(row.get("email")) or "").lower(),
			"mobile": _text(row.get("mobile")),
		}
		for field, field_label in (
			("referee_name", _("Name")),
			("current_designation_org", _("Current Designation and Organization")),
			("relationship", _("Nature of Relationship")),
			("email", _("Email Address")),
			("mobile", _("Mobile Number")),
		):
			errors.require(values[field], f"{label}: {field_label}", f"{key}.{field}")
		if values["email"] and not validate_email_address(values["email"]):
			errors.add(_("{0}: enter a valid email address.").format(label), f"{key}.email")
		if values["email"] and values["email"] == email:
			errors.add(_("{0}: you cannot give your own email as a referee.").format(label), f"{key}.email")
		if values["mobile"] and mobile_error(values["mobile"]):
			errors.add(f"{label}: {mobile_error(values['mobile'])}", f"{key}.mobile")
		references.append(values)
	if len(references) < 2:
		errors.add(_("Two referees are required."), "ref.1.referee_name")
	elif references[0]["email"] and references[0]["email"] == references[1]["email"]:
		errors.add(_("The two referees must be different people."), "ref.1.email")

	# --- source, money, joining
	source = app.get("source")
	if not source or not frappe.db.exists("Candidate Source", {"name": source, "is_active": 1}):
		errors.add(_("Tell us how you heard about this position."), "application.source")
	current_salary = _number(app.get("current_salary"), _("Current Salary (Per Month)"), errors, "application.current_salary")
	expected_salary = _number(app.get("expected_salary"), _("Expected Salary"), errors, "application.expected_salary")
	doj = _date(app.get("earliest_doj"), _("Earliest Date Of Joining"), errors, "application.earliest_doj")
	if not app.get("earliest_doj"):
		errors.add(_("Earliest Date Of Joining is required."), "application.earliest_doj")
	elif doj and doj < getdate(today()):
		errors.add(_("Earliest Date Of Joining cannot be in the past."), "application.earliest_doj")

	# --- documents
	resume = upload(app.get("resume_attachment"), _("Resume / CV"), True, "application.resume_attachment")
	sop = upload(app.get("sop_attachment"), _("Statement of Purpose"), True, "application.sop_attachment")
	additional = upload(app.get("additional_attachment"), _("Additional Documents"), False, "application.additional_attachment")

	given_docs = {d.get("document_type"): d.get("attachment") for d in app.get("documents") or []}
	documents = []
	for spec in get_required_documents(job):
		field = f"doc.{spec['document_type']}"
		url = given_docs.get(spec["document_type"])
		if not url:
			if spec["mandatory"]:
				errors.add(_("{0} is required.").format(spec["label"]), field)
			continue
		before = len(errors.messages)
		name = check_file(url, user, spec, spec["label"], errors, upload_tokens)
		if len(errors.messages) > before:
			errors.fields.setdefault(field, errors.messages[-1])
		if name:
			files.append((name, spec["label"]))
		documents.append(
			{
				"document_type": spec["document_type"],
				"is_mandatory": "Yes" if spec["mandatory"] else "No",
				"attachment": url,
				"uploaded_on": now_datetime(),
			}
		)

	if not cint(data.get("declaration_accepted")):
		errors.add(_("You must accept the declaration to submit."), "declaration")

	errors.raise_if_any()

	candidate_fields = {
		"full_name": full_name,
		"mobile_number": mobile,
		"date_of_birth": dob,
		"gender": gender,
		"address": address,
	}
	application_fields = {
		"job_opening": job.name,
		"track": job.track,
		"source": source,
		"current_salary": flt(current_salary),
		"expected_salary": flt(expected_salary),
		"earliest_doj": doj,
		"overall_experience_years": overall,
		"relevant_experience_years": relevant,
		"notice_period": notice_period,
		"resume_attachment": resume,
		"sop_attachment": sop,
		"additional_attachment": additional,
		"qualifications": qualifications,
		"employment_history": employment,
		"references": references,
		"screening_answers": screening,
		"documents": documents,
		"declaration_accepted": 1,
		"declaration_accepted_on": now_datetime(),
	}
	return candidate_fields, application_fields, files


# --------------------------------------------------------- stored file names

URL_FIELDS = ("resume_attachment", "sop_attachment", "additional_attachment")
CHILD_URL_FIELDS = {
	"qualifications": ("transcript_attachment", "certificate_attachment"),
	"documents": ("attachment",),
}


def _slug(text):
	return re.sub(r"[^A-Za-z0-9]+", "-", text or "").strip("-")[:50] or "Document"


def name_uploads_for_application(application, files):
	"""Store each upload as "<Application ID>_<what it is>.<ext>", e.g.
	PWY-APP-2026-000014_Resume-CV.pdf, and point the application at it.

	The file is copied, not moved: Frappe stores identical content once and
	several File records may share it. Old copies nobody uses any more are
	removed only after the transaction commits, so a failed submission
	leaves nothing broken. Call before application.insert()."""
	renamed = {}  # old file_url -> new file_url
	stale = set()
	for file_name, label in files:
		file = frappe.db.get_value("File", file_name, ["file_url", "is_private"], as_dict=True)
		if not file or file.file_url in renamed:
			continue
		old_path = frappe.utils.get_files_path(file.file_url.rsplit("/", 1)[-1], is_private=file.is_private)
		if not os.path.exists(old_path):
			continue
		extension = os.path.splitext(file.file_url)[1].lower()
		base = f"{application.application_id}_{_slug(label)}"
		new_name, n = f"{base}{extension}", 1
		while os.path.exists(frappe.utils.get_files_path(new_name, is_private=file.is_private)):
			n += 1
			new_name = f"{base}-{n}{extension}"
		shutil.copyfile(old_path, frappe.utils.get_files_path(new_name, is_private=file.is_private))
		new_url = f"{'/private' if file.is_private else ''}/files/{new_name}"
		frappe.db.set_value("File", file_name, {"file_name": new_name, "file_url": new_url}, update_modified=False)
		renamed[file.file_url] = new_url
		stale.add((file.file_url, old_path))

	for field in URL_FIELDS:
		if application.get(field) in renamed:
			application.set(field, renamed[application.get(field)])
	for table, fields in CHILD_URL_FIELDS.items():
		for row in application.get(table) or []:
			for field in fields:
				if row.get(field) in renamed:
					row.set(field, renamed[row.get(field)])

	def remove_unused_originals():
		for old_url, old_path in stale:
			if not frappe.db.exists("File", {"file_url": old_url}) and os.path.exists(old_path):
				os.remove(old_path)

	frappe.db.after_commit.add(remove_unused_originals)
