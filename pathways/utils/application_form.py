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

import os
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate, now_datetime, today, validate_email_address

YES_NO = ("Yes", "No")
MOBILE_RE = re.compile(r"^\+?[0-9][0-9 \-]{8,16}[0-9]$")


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
	"""Collect every problem so the candidate sees them all at once."""

	def __init__(self):
		self.messages = []

	def add(self, message):
		self.messages.append(message)

	def require(self, value, label):
		if value is None or (isinstance(value, str) and not value.strip()):
			self.add(_("{0} is required.").format(label))
			return False
		return True

	def raise_if_any(self):
		if self.messages:
			frappe.throw(
				"<ul>" + "".join(f"<li>{frappe.utils.escape_html(m)}</li>" for m in self.messages) + "</ul>",
				title=_("Please correct the following"),
			)


def _text(value):
	return (value or "").strip() if isinstance(value, str) else value


def _percentage(value, label, errors):
	try:
		number = float(str(value).strip().rstrip("%"))
	except (TypeError, ValueError):
		errors.add(_("{0}: enter the percentage as a number (convert CGPA using your university's table).").format(label))
		return None
	if not 0 <= number <= 100:
		errors.add(_("{0}: percentage must be between 0 and 100.").format(label))
	return number


def _year(value, label, errors):
	year = cint(value)
	if not 1950 <= year <= getdate(today()).year + 1:
		errors.add(_("{0}: enter a valid year.").format(label))
	return year


def _date(value, label, errors):
	if not value:
		return None
	try:
		return getdate(value)
	except Exception:
		errors.add(_("{0}: invalid date.").format(label))
		return None


def check_file(file_url, user, rule, label, errors):
	"""The upload must exist, belong to this candidate, be private, not be
	attached to anything else yet, and match the size/format rule — so a
	candidate can never point their application at someone else's file."""
	if not file_url:
		return None
	file = frappe.db.get_value(
		"File",
		{"file_url": file_url, "owner": user},
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


def validate_submission(job, data, user):
	"""Validate a submission against the job's form. Returns
	(candidate_fields, application_fields, file_names) ready to save."""
	errors = FormErrors()
	rule = default_upload_rule()
	files = []

	def upload(url, label, required):
		if not url:
			if required:
				errors.add(_("{0} is required.").format(label))
			return None
		name = check_file(url, user, rule, label, errors)
		if name:
			files.append(name)
		return url

	# --- personal details
	personal = data.get("candidate") or {}
	full_name = _text(personal.get("full_name"))
	mobile = _text(personal.get("mobile_number"))
	errors.require(full_name, _("Name"))
	if errors.require(mobile, _("Mobile Number")) and not MOBILE_RE.match(mobile):
		errors.add(_("Enter a valid mobile number."))
	dob = _date(personal.get("date_of_birth"), _("Date of Birth"), errors)
	if not personal.get("date_of_birth"):
		errors.add(_("Date of Birth is required."))
	elif dob and (dob >= getdate(today()) or getdate(today()).year - dob.year > 100):
		errors.add(_("Enter a valid Date of Birth."))
	gender = personal.get("gender")
	if gender not in ("Female", "Male", "Prefer not to say", "Other"):
		errors.add(_("Gender is required."))
	address = _text(personal.get("address"))
	errors.require(address, _("Address for Correspondence"))

	# --- qualifications
	app = data.get("application") or {}
	qualifications = []
	for level, label, required in (
		("Undergraduate", _("Graduate Degree"), True),
		("Postgraduate", _("Post Graduate Degree"), bool(cint(job.require_postgraduate))),
	):
		row = next((q for q in app.get("qualifications") or [] if q.get("degree_level") == level), None)
		filled = row and any(_text(row.get(k)) for k in ("degree_name", "other_institution", "year_of_graduation"))
		if not filled:
			if required:
				errors.add(_("{0} details are required.").format(label))
			continue
		errors.require(_text(row.get("degree_name")), _("{0}: Name of the Degree").format(label))
		errors.require(_text(row.get("other_institution")), _("{0}: College / University").format(label))
		_year(row.get("year_of_graduation"), label, errors)
		_percentage(row.get("percentage_or_cgpa"), label, errors)
		errors.require(_text(row.get("division_grade")), _("{0}: Division / Grade").format(label))
		errors.require(_text(row.get("specialization")), _("{0}: Specialization").format(label))
		qualifications.append(
			{
				"degree_level": level,
				"degree_name": _text(row.get("degree_name")),
				"other_institution": _text(row.get("other_institution")),
				"year_of_graduation": cint(row.get("year_of_graduation")),
				"percentage_or_cgpa": str(row.get("percentage_or_cgpa") or "").strip(),
				"division_grade": _text(row.get("division_grade")),
				"specialization": _text(row.get("specialization")),
				"transcript_attachment": upload(row.get("transcript_attachment"), _("{0}: Transcript").format(label), required),
				"certificate_attachment": upload(
					row.get("certificate_attachment"), _("{0}: Degree Certificate").format(label), required
				),
			}
		)

	# --- experience
	overall = flt(app.get("overall_experience_years"), 1)
	relevant = flt(app.get("relevant_experience_years"), 1)
	if app.get("overall_experience_years") in (None, ""):
		errors.add(_("Overall work experience is required (enter 0 if none)."))
	if app.get("relevant_experience_years") in (None, ""):
		errors.add(_("Relevant work experience is required (enter 0 if none)."))
	if overall < 0 or relevant < 0 or overall > 60:
		errors.add(_("Enter valid years of experience."))
	if relevant > overall:
		errors.add(_("Relevant experience cannot exceed overall experience."))

	employment = []
	for i, row in enumerate(app.get("employment_history") or [], start=1):
		if not any(_text(row.get(k)) for k in ("designation", "employer_name", "from_date")):
			continue
		label = _("Organisation #{0}").format(i)
		errors.require(_text(row.get("designation")), _("{0}: Designation").format(label))
		errors.require(_text(row.get("employer_name")), _("{0}: Name of the employer").format(label))
		start = _date(row.get("from_date"), _("{0}: From Date").format(label), errors)
		if not row.get("from_date"):
			errors.add(_("{0}: From Date is required.").format(label))
		is_current = cint(row.get("is_current"))
		end = None if is_current else _date(row.get("to_date"), _("{0}: To Date").format(label), errors)
		if not is_current and not row.get("to_date"):
			errors.add(_("{0}: To Date is required (or tick 'Currently working here').").format(label))
		if start and end and end < start:
			errors.add(_("{0}: To Date cannot be before From Date.").format(label))
		if start and start > getdate(today()):
			errors.add(_("{0}: From Date cannot be in the future.").format(label))
		if i == 1:
			errors.require(_text(row.get("key_responsibilities")), _("{0}: Key Responsibilities").format(label))
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
		errors.add(_("Add at least your most recent organisation under Professional Experience."))
	notice_period = _text(app.get("notice_period"))
	if employment:
		errors.require(notice_period, _("Current Notice Period"))

	# --- screening questions
	answers_in = {cint(a.get("idx")): a for a in app.get("screening_answers") or []}
	screening = []
	for q in job.get("screening_questions") or []:
		given = answers_in.get(q.idx) or {}
		answer = _text(str(given.get("answer") if given.get("answer") is not None else ""))
		details = _text(given.get("details"))
		if not answer:
			if cint(q.is_mandatory):
				errors.add(_("Please answer: {0}").format(q.question))
			screening.append({"question": q.question, "answer_type": q.answer_type, "answer": "", "details": ""})
			continue
		if q.answer_type == "Yes/No" and answer not in YES_NO:
			errors.add(_("Answer Yes or No: {0}").format(q.question))
		elif q.answer_type == "Single Choice":
			options = [o.strip() for o in (q.options or "").splitlines() if o.strip()]
			if answer not in options:
				errors.add(_("Choose one of the listed options: {0}").format(q.question))
		elif q.answer_type == "Number":
			try:
				float(answer)
			except ValueError:
				errors.add(_("Enter a number: {0}").format(q.question))
		if q.answer_type == "Yes/No" and cint(q.ask_details_if_yes) and answer == "Yes" and not details:
			errors.add(_("Please add details for: {0}").format(q.question))
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
		values = {
			"referee_name": _text(row.get("referee_name")),
			"current_designation_org": _text(row.get("current_designation_org")),
			"relationship": _text(row.get("relationship")),
			"email": (_text(row.get("email")) or "").lower(),
			"mobile": _text(row.get("mobile")),
		}
		for key, field_label in (
			("referee_name", _("Name")),
			("current_designation_org", _("Current Designation and Organization")),
			("relationship", _("Nature of Relationship")),
			("email", _("Email Address")),
			("mobile", _("Mobile Number")),
		):
			errors.require(values[key], f"{label}: {field_label}")
		if values["email"] and not validate_email_address(values["email"]):
			errors.add(_("{0}: enter a valid email address.").format(label))
		if values["email"] and values["email"] == user:
			errors.add(_("{0}: you cannot give your own email as a referee.").format(label))
		if values["mobile"] and not MOBILE_RE.match(values["mobile"]):
			errors.add(_("{0}: enter a valid mobile number.").format(label))
		references.append(values)
	if len(references) < 2:
		errors.add(_("Two referees are required."))
	elif references[0]["email"] and references[0]["email"] == references[1]["email"]:
		errors.add(_("The two referees must be different people."))

	# --- source, money, joining
	source = app.get("source")
	if not source or not frappe.db.exists("Candidate Source", {"name": source, "is_active": 1}):
		errors.add(_("Tell us how you heard about this position."))
	for key, label in (("current_salary", _("Current Salary (Per Month)")), ("expected_salary", _("Expected Salary"))):
		if app.get(key) in (None, ""):
			errors.add(_("{0} is required (enter 0 if not applicable).").format(label))
		elif flt(app.get(key)) < 0:
			errors.add(_("{0} cannot be negative.").format(label))
	doj = _date(app.get("earliest_doj"), _("Earliest Date Of Joining"), errors)
	if not app.get("earliest_doj"):
		errors.add(_("Earliest Date Of Joining is required."))
	elif doj and doj < getdate(today()):
		errors.add(_("Earliest Date Of Joining cannot be in the past."))

	# --- documents
	resume = upload(app.get("resume_attachment"), _("Resume / CV"), True)
	sop = upload(app.get("sop_attachment"), _("Statement of Purpose"), True)
	additional = upload(app.get("additional_attachment"), _("Additional Documents"), False)

	given_docs = {d.get("document_type"): d.get("attachment") for d in app.get("documents") or []}
	documents = []
	for spec in get_required_documents(job):
		url = given_docs.get(spec["document_type"])
		if not url:
			if spec["mandatory"]:
				errors.add(_("{0} is required.").format(spec["label"]))
			continue
		name = check_file(url, user, spec, spec["label"], errors)
		if name:
			files.append(name)
		documents.append(
			{
				"document_type": spec["document_type"],
				"is_mandatory": "Yes" if spec["mandatory"] else "No",
				"attachment": url,
				"uploaded_on": now_datetime(),
			}
		)

	if not cint(data.get("declaration_accepted")):
		errors.add(_("You must accept the declaration to submit."))

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
		"current_salary": flt(app.get("current_salary")),
		"expected_salary": flt(app.get("expected_salary")),
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
