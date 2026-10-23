# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Documents page > Share with panel: the recruitment team chooses which of
the candidates' documents each Selection Committee panellist should read.
Shares are recorded per application and panellist (Panel Document Share),
each panellist gets one email with a link, and reads them on Interview
Panel > Shared documents. Files are never attached to the email.

Workflow step 16 also lists job-level files for the panel: the
Notification, panel details, blank Interview Assessment sheets, the
Shortlisting Note (and its attachments), the HR interaction notes and the
interview schedule. Those are shared per job and panellist (Panel Job File
Share) and generated when opened, so the panel always reads the current
version."""

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from pathways.api.application import _application_documents
from pathways.api.interviews import _can_manage
from pathways.api.panel import _my_committees, _panel_members

SHARE = "Panel Document Share"


def _require_manage():
	if not _can_manage():
		frappe.throw(_("Only the recruitment team can share documents with the panel."), frappe.PermissionError)


def _load_apps(applications):
	names = frappe.parse_json(applications) if isinstance(applications, str) else applications
	names = list(dict.fromkeys(n for n in names or [] if n))
	if not names:
		frappe.throw(_("Choose at least one candidate."))
	apps = []
	for name in names:
		app = frappe.get_doc("Application", name)
		app.check_permission("read")
		apps.append(app)
	jobs = {a.job_opening for a in apps}
	if len(jobs) > 1:
		frappe.throw(_("Choose candidates from one job opening at a time: each job has its own panel."))
	return apps, jobs.pop()


def _committee_members(job_opening):
	return _panel_members(frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, "name"))


def _unique_documents(app):
	"""The application's documents, one per label, in reading order."""
	seen = {}
	for d in _application_documents(app):
		seen.setdefault(d["label"], d)
	return list(seen.values())


def _candidate_names(apps):
	return dict(
		frappe.get_all("Candidate", filters={"name": ["in", list({a.candidate for a in apps})]}, fields=["name", "full_name"], as_list=True)
	)


def _shared_labels(application_names, panelists=None):
	"""{(application, panelist): [labels]} of what is shared now."""
	filters = {"application": ["in", application_names]}
	if panelists is not None:
		filters["panelist"] = ["in", panelists or [""]]
	shares = frappe.get_all(SHARE, filters=filters, fields=["name", "application", "panelist"])
	if not shares:
		return {}
	labels = {}
	for r in frappe.get_all(
		"Panel Shared Document",
		filters={"parenttype": SHARE, "parent": ["in", [s.name for s in shares]]},
		fields=["parent", "document_label"],
		order_by="idx asc",
	):
		labels.setdefault(r.parent, []).append(r.document_label)
	return {(s.application, s.panelist): labels.get(s.name, []) for s in shares}


@frappe.whitelist()
def get_share_options(applications):
	"""What the Share with panel dialog needs: the job's panel, every
	document type the chosen candidates uploaded (with how many have it),
	and what each panellist already has."""
	_require_manage()
	apps, job_opening = _load_apps(applications)
	members = _committee_members(job_opening)
	names = _candidate_names(apps)

	documents = {}
	for app in apps:
		for d in _unique_documents(app):
			entry = documents.setdefault(d["label"], {"label": d["label"], "group": d["group"], "count": 0})
			entry["count"] += 1

	current = _shared_labels([a.name for a in apps], members)
	# {panelist: {label: how many of the chosen candidates it is shared for}}
	shared = {m: {} for m in members}
	for (application, panelist), labels in current.items():
		for label in labels:
			shared[panelist][label] = shared[panelist].get(label, 0) + 1

	return {
		"job": frappe.db.get_value("Job Opening", job_opening, ["name", "job_title", "position"], as_dict=True),
		"panel": [{"user": m, "full_name": frappe.utils.get_fullname(m)} for m in members],
		"documents": list(documents.values()),
		"applications": [{"name": a.name, "application_id": a.application_id, "candidate_name": names.get(a.candidate) or ""} for a in apps],
		"shared": shared,
	}


@frappe.whitelist(methods=["POST"])
def share_with_panel(applications, changes, note=None, notify=1):
	"""Apply the dialog's changes, {panelist: {label: true | false}}: true
	shares that document of every chosen candidate who has it, false stops
	sharing it. Labels left out stay as they are. Emails each panellist who
	got something new."""
	_require_manage()
	apps, job_opening = _load_apps(applications)
	changes = frappe.parse_json(changes) if isinstance(changes, str) else changes
	changes = changes or {}
	members = _committee_members(job_opening)
	if not members:
		frappe.throw(_("This job has no Selection Committee yet. Set up the panel first."))
	outside = [p for p in changes if p not in members]
	if outside:
		frappe.throw(_("{0} is not on this job's Selection Committee.").format(", ".join(outside)))

	note = (note or "").strip()
	names = _candidate_names(apps)
	available = {a.name: _unique_documents(a) for a in apps}
	added, added_count, removed = {}, 0, 0
	for panelist, cells in changes.items():
		give = {label for label, on in (cells or {}).items() if on}
		take = {label for label, on in (cells or {}).items() if not on}
		if not give and not take:
			continue
		for app in apps:
			docs = available[app.name]
			name = frappe.db.get_value(SHARE, {"application": app.name, "panelist": panelist}, "name")
			doc = frappe.get_doc(SHARE, name) if name else None
			current = [r.document_label for r in doc.documents] if doc else []
			keep = [label for label in current if label not in take]
			new = [d["label"] for d in docs if d["label"] in give and d["label"] not in keep]
			removed += len(current) - len(keep)
			if not new and len(keep) == len(current):
				continue
			if not keep and not new:
				frappe.delete_doc(SHARE, doc.name, ignore_permissions=True)
				continue
			# Reading order of the application; anything no longer uploaded stays at the end.
			groups = {d["label"]: d["group"] for d in docs}
			final = [d["label"] for d in docs if d["label"] in keep or d["label"] in new]
			final += [label for label in keep if label not in groups]
			if not doc:
				doc = frappe.new_doc(SHARE)
				doc.update({"job_opening": job_opening, "application": app.name, "panelist": panelist})
			doc.update(
				{
					"candidate_name": names.get(app.candidate) or "",
					"panelist_name": frappe.utils.get_fullname(panelist),
					"shared_by": frappe.session.user,
					"last_shared_on": now_datetime(),
				}
			)
			if new and note:
				doc.note = note
			doc.set("documents", [{"document_label": label, "document_group": groups.get(label, "")} for label in final])
			doc.save(ignore_permissions=True)
			if new:
				added_count += len(new)
				added.setdefault(panelist, []).append({"name": names.get(app.candidate) or "", "application_id": app.application_id, "documents": ", ".join(new)})

	emailed = 0
	if cint(notify) and added:
		from pathways.utils.communication import job_email_context, send_event

		job = frappe.get_doc("Job Opening", job_opening)
		base = job_email_context(job)
		for panelist, candidates in added.items():
			context = dict(base)
			# Email Templates are not auto-escaped: escape what people typed.
			esc = frappe.utils.escape_html
			context.update(
				{
					"candidates": [{k: esc(v or "") for k, v in c.items()} for c in candidates],
					"candidate_count": len(candidates),
					"note": esc(note),
					"documents_link": frappe.utils.get_url(f"/pathways/panel/documents?job={job_opening}"),
					"shared_by": frappe.utils.get_fullname(frappe.session.user),
				}
			)
			send_event("panel_documents_shared", "Job Opening", job_opening, context, approvers=[panelist])
			emailed += 1
	return {
		"added": added_count,
		"removed": removed,
		"panellists": len(added),
		"emailed": emailed if frappe.db.exists("Recruitment Email Rule", {"name": "panel_documents_shared", "enabled": 1}) else 0,
	}


@frappe.whitelist()
def get_shared_documents(job_opening=None):
	"""Interview Panel > Shared documents: what was shared with this
	panellist (for jobs whose panel they are still on). The recruitment team
	sees every share, with whom it went to."""
	manage = _can_manage()
	filters = {}
	if not manage:
		filters["panelist"] = frappe.session.user
	if job_opening:
		filters["job_opening"] = job_opening
	shares = frappe.get_all(
		SHARE,
		filters=filters,
		fields=["name", "job_opening", "application", "candidate_name", "panelist", "panelist_name", "note", "last_shared_on", "shared_by"],
		order_by="last_shared_on desc",
	)
	if not manage:
		on_panel = set(frappe.get_all("Selection Committee", filters={"name": ["in", _my_committees() or [""]]}, pluck="job_opening"))
		shares = [s for s in shares if s.job_opening in on_panel]
	job_rows = job_file_rows(job_opening, manage)
	if not shares:
		return {"rows": [], "job_files": job_rows, "can_manage": 1 if manage else 0}

	labels = {}
	for r in frappe.get_all(
		"Panel Shared Document", filters={"parenttype": SHARE, "parent": ["in", [s.name for s in shares]]}, fields=["parent", "document_label"], order_by="idx asc"
	):
		labels.setdefault(r.parent, []).append(r.document_label)
	jobs = {
		j.name: j for j in frappe.get_all("Job Opening", filters={"name": ["in", list({s.job_opening for s in shares})]}, fields=["name", "job_title", "position"])
	}
	apps = {}
	rows = []
	for s in shares:
		if s.application not in apps:
			if not frappe.db.exists("Application", s.application):
				continue
			apps[s.application] = frappe.get_doc("Application", s.application)
		app = apps[s.application]
		wanted = labels.get(s.name, [])
		# Resolve the files now, so a re-uploaded document shows its latest file.
		docs = [d for d in _application_documents(app) if d["label"] in wanted]
		job = jobs.get(s.job_opening) or frappe._dict()
		rows.append(
			{
				"name": s.name,
				"job_opening": s.job_opening,
				"job_title": job.get("job_title") or s.job_opening,
				"position": job.get("position") or "",
				"application": s.application,
				"application_id": app.application_id,
				"candidate_name": s.candidate_name,
				"panelist": s.panelist,
				"panelist_name": s.panelist_name or frappe.utils.get_fullname(s.panelist),
				"note": s.note or "",
				"shared_on": s.last_shared_on,
				"shared_by": frappe.utils.get_fullname(s.shared_by) if s.shared_by else "",
				"documents": docs,
			}
		)
	return {"rows": rows, "job_files": job_rows, "can_manage": 1 if manage else 0}


def shared_for_panelist(application, panelist):
	"""The documents of `application` shared with `panelist`, resolved to
	the current files, for the Interview Assessment Form."""
	labels = _shared_labels([application], [panelist]).get((application, panelist))
	if not labels:
		return []
	return [d for d in _application_documents(frappe.get_doc("Application", application)) if d["label"] in labels]


# ------------------------------------------------------- job-level files (step 16)

JOB_SHARE = "Panel Job File Share"
NOTIFICATION = "Recruitment Notification"
PANEL_DETAILS = "Panel details"
BLANK_FORMS = "Blank assessment sheets"
SHORTLISTING_NOTE = "Shortlisting Note"
HR_NOTES = "HR interaction notes"
SCHEDULE = "Interview schedule"
NOTE_ATTACHMENT_PREFIX = "Shortlisting Note: "


def _notification_file(job_opening):
	from pathways.api.job_notice import notice_for

	notice = notice_for(job_opening).get("notification") or {}
	return notice.get("notification_attachment") or frappe.db.get_value("Job Opening", job_opening, "jd_attachment")


def job_files(job_opening):
	"""The job-level files that exist for this job: [{label, group, kind}]."""
	files = []
	if _notification_file(job_opening):
		files.append({"label": NOTIFICATION, "group": _("Job"), "kind": "pdf"})
	if frappe.db.exists("Selection Committee", {"job_opening": job_opening}):
		files.append({"label": PANEL_DETAILS, "group": _("Job"), "kind": "pdf"})
		files.append({"label": BLANK_FORMS, "group": _("Job"), "kind": "pdf"})
	note = frappe.db.get_value("Shortlisting Note", {"job_opening": job_opening}, "name")
	if note:
		files.append({"label": SHORTLISTING_NOTE, "group": _("Shortlisting"), "kind": "pdf"})
		for r in frappe.get_all("Shortlisting Note Attachment", filters={"parenttype": "Shortlisting Note", "parent": note}, fields=["label", "attachment"], order_by="idx asc"):
			ext = (r.attachment or "").rsplit(".", 1)[-1].lower()
			files.append({"label": _safe_label(NOTE_ATTACHMENT_PREFIX + (r.label or "")), "group": _("Shortlisting"), "kind": "pdf" if ext == "pdf" else "other"})
	apps = frappe.get_all("Application", filters={"job_opening": job_opening}, pluck="name")
	if apps and frappe.db.exists("Interview", {"application": ["in", apps], "round_type": "HR Interaction", "status": ["!=", "Cancelled"]}):
		files.append({"label": HR_NOTES, "group": _("Interviews"), "kind": "pdf"})
	if apps and frappe.db.exists("Interview", {"application": ["in", apps], "status": ["!=", "Cancelled"]}):
		files.append({"label": SCHEDULE, "group": _("Interviews"), "kind": "pdf"})
	return files


def _safe_label(label):
	# Panel Shared Document.document_label is a Data field (140 characters).
	return label[:140]


def _file_bytes(file_url):
	name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not name:
		frappe.throw(_("The file {0} is no longer available.").format(file_url))
	doc = frappe.get_doc("File", name)
	return doc.get_content(), doc.file_name


PANEL_HTML = """
<style>
	body { font-family: Arial, sans-serif; font-size: 12px; color: #111; }
	h1 { font-size: 15px; text-align: center; margin: 0 0 2px; }
	h2 { font-size: 12px; text-align: center; margin: 0 0 12px; }
	table { width: 100%; border-collapse: collapse; }
	td, th { border: 1px solid #555; padding: 6px; text-align: left; }
	th { background: #f2e6e8; }
</style>
{{ letterhead }}
<h2>SELECTION COMMITTEE | {{ job_title | upper }}</h2>
<p><b>Date of interviews:</b> {{ date or "To be confirmed" }}{% if time %} &nbsp; <b>From:</b> {{ time }}{% endif %}</p>
<table>
	<tr><th style="width:6%">Sl. No.</th><th>Name</th><th>Designation</th><th style="width:16%">Member</th></tr>
	{% for m in members %}<tr><td>{{ loop.index }}</td><td>{{ m.name }}</td><td>{{ m.designation }}</td><td>{{ m.kind }}</td></tr>{% endfor %}
</table>
"""


def _panel_details_pdf(job_opening):
	from frappe.utils.pdf import get_pdf

	from pathways.utils.letterhead import letterhead_html

	committee = frappe.get_doc("Selection Committee", frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, "name"))
	members = [
		{"name": frappe.utils.get_fullname(m.member), "designation": m.designation_label or "", "kind": _("External expert") if m.is_external_expert else _("Internal")}
		for m in committee.members
	]
	html = frappe.render_template(
		PANEL_HTML,
		{
			"letterhead": letterhead_html(),
			"job_title": frappe.db.get_value("Job Opening", job_opening, "job_title"),
			"date": frappe.utils.formatdate(committee.scheduled_date, "dd MMM yyyy") if committee.scheduled_date else "",
			"time": frappe.utils.format_time(committee.scheduled_time, "h:mm a") if committee.scheduled_time else "",
			"members": members,
		},
	)
	return get_pdf(html, {"page-size": "A4"})


def job_file_content(job_opening, label, panelist=None):
	"""(bytes, file name) of one job-level file. panelist: the blank forms
	are printed for that panellist only."""
	from pathways.api import interviews, panel

	job_title = frappe.db.get_value("Job Opening", job_opening, "job_title")
	if label == NOTIFICATION:
		url = _notification_file(job_opening)
		if not url:
			frappe.throw(_("This job has no notification file."))
		return _file_bytes(url)
	if label == PANEL_DETAILS:
		return _panel_details_pdf(job_opening), f"Selection Committee - {job_title}.pdf"
	if label == BLANK_FORMS:
		members = [{"user": panelist, "full_name": frappe.utils.get_fullname(panelist)}] if panelist else None
		if members is None:
			members = [{"user": m, "full_name": frappe.utils.get_fullname(m)} for m in _committee_members(job_opening)]
		return panel.assessment_forms_pdf(job_opening, blank=1, members_override=members)
	if label == SHORTLISTING_NOTE:
		return interviews.shortlisting_note_pdf(job_opening), f"Shortlisting Note - {job_title}.pdf"
	if label.startswith(NOTE_ATTACHMENT_PREFIX):
		note = frappe.db.get_value("Shortlisting Note", {"job_opening": job_opening}, "name")
		for r in frappe.get_all("Shortlisting Note Attachment", filters={"parenttype": "Shortlisting Note", "parent": note or ""}, fields=["label", "attachment"]):
			if _safe_label(NOTE_ATTACHMENT_PREFIX + (r.label or "")) == label:
				return _file_bytes(r.attachment)
		frappe.throw(_("That attachment is no longer on the Shortlisting Note."))
	if label == HR_NOTES:
		return panel.hr_notes_pdf(job_opening), f"HR Interaction Notes - {job_title}.pdf"
	if label == SCHEDULE:
		round_type = "Final" if frappe.db.exists(
			"Interview", {"application": ["in", frappe.get_all("Application", filters={"job_opening": job_opening}, pluck="name") or [""]], "round_type": "Final", "status": ["!=", "Cancelled"]}
		) else "HR Interaction"
		return interviews.schedule_pdf(job_opening, round_type), f"Interview Schedule - {job_title}.pdf"
	frappe.throw(_("Unknown file."))


def _job_shared(job_opening, panelists=None):
	"""{panelist: [labels]} shared now."""
	filters = {"job_opening": job_opening}
	if panelists is not None:
		filters["panelist"] = ["in", panelists or [""]]
	shares = frappe.get_all(JOB_SHARE, filters=filters, fields=["name", "panelist"])
	if not shares:
		return {}
	labels = {}
	for r in frappe.get_all("Panel Shared Document", filters={"parenttype": JOB_SHARE, "parent": ["in", [s.name for s in shares]]}, fields=["parent", "document_label"], order_by="idx asc"):
		labels.setdefault(r.parent, []).append(r.document_label)
	return {s.panelist: labels.get(s.name, []) for s in shares}


@frappe.whitelist()
def get_job_share_options(job_opening):
	"""Share with panel > Job files: the job's files, its panel and what each
	panellist has already."""
	_require_manage()
	members = _committee_members(job_opening)
	shared = _job_shared(job_opening, members)
	return {
		"job": frappe.db.get_value("Job Opening", job_opening, ["name", "job_title", "position"], as_dict=True),
		"panel": [{"user": m, "full_name": frappe.utils.get_fullname(m)} for m in members],
		"files": job_files(job_opening),
		"shared": {m: {label: 1 for label in shared.get(m, [])} for m in members},
	}


@frappe.whitelist(methods=["POST"])
def share_job_files(job_opening, changes, note=None, notify=1):
	"""Apply {panelist: {label: true | false}} for the job's files and email
	each panellist who got something new."""
	_require_manage()
	changes = frappe.parse_json(changes) if isinstance(changes, str) else (changes or {})
	members = _committee_members(job_opening)
	if not members:
		frappe.throw(_("This job has no Selection Committee yet. Set up the panel first."))
	outside = [p for p in changes if p not in members]
	if outside:
		frappe.throw(_("{0} is not on this job's Selection Committee.").format(", ".join(outside)))
	available = job_files(job_opening)
	order = [f["label"] for f in available]
	groups = {f["label"]: f["group"] for f in available}
	note = (note or "").strip()
	added, added_count, removed = {}, 0, 0
	for panelist, cells in changes.items():
		give = {label for label, on in (cells or {}).items() if on and label in groups}
		take = {label for label, on in (cells or {}).items() if not on}
		name = frappe.db.get_value(JOB_SHARE, {"job_opening": job_opening, "panelist": panelist}, "name")
		doc = frappe.get_doc(JOB_SHARE, name) if name else None
		current = [r.document_label for r in doc.files] if doc else []
		keep = [label for label in current if label not in take]
		new = [label for label in order if label in give and label not in keep]
		removed += len(current) - len(keep)
		if not new and len(keep) == len(current):
			continue
		if not keep and not new:
			frappe.delete_doc(JOB_SHARE, doc.name, ignore_permissions=True)
			continue
		if not doc:
			doc = frappe.new_doc(JOB_SHARE)
			doc.update({"job_opening": job_opening, "panelist": panelist})
		doc.update({"panelist_name": frappe.utils.get_fullname(panelist), "shared_by": frappe.session.user, "last_shared_on": now_datetime()})
		if new and note:
			doc.note = note
		final = [label for label in order if label in keep or label in new] + [label for label in keep if label not in groups]
		doc.set("files", [{"document_label": label, "document_group": groups.get(label, "")} for label in final])
		doc.save(ignore_permissions=True)
		if new:
			added_count += len(new)
			added[panelist] = new
	emailed = 0
	if cint(notify) and added:
		from pathways.utils.communication import job_email_context, send_event

		base = job_email_context(frappe.get_doc("Job Opening", job_opening))
		esc = frappe.utils.escape_html
		for panelist, labels in added.items():
			context = dict(base)
			context.update(
				{
					"files": [esc(label) for label in labels],
					"note": esc(note),
					"documents_link": frappe.utils.get_url(f"/pathways/panel/documents?job={job_opening}"),
					"shared_by": frappe.utils.get_fullname(frappe.session.user),
				}
			)
			send_event("panel_job_files_shared", "Job Opening", job_opening, context, approvers=[panelist])
			emailed += 1
	return {
		"added": added_count,
		"removed": removed,
		"panellists": len(added),
		"emailed": emailed if frappe.db.exists("Recruitment Email Rule", {"name": "panel_job_files_shared", "enabled": 1}) else 0,
	}


@frappe.whitelist()
def download_job_file(job_opening, label):
	"""Open one job-level file: the recruitment team any of them, a
	panellist only what was shared with them while they are on the panel."""
	user = frappe.session.user
	if _can_manage():
		panelist = None
	else:
		if user not in _committee_members(job_opening) or label not in _job_shared(job_opening, [user]).get(user, []):
			frappe.throw(_("This file has not been shared with you."), frappe.PermissionError)
		panelist = user
	content, filename = job_file_content(job_opening, label, panelist)
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"


def job_file_rows(job_opening=None, manage=False):
	"""Interview Panel > Shared documents: the job files shared, per panellist."""
	filters = {}
	if not manage:
		filters["panelist"] = frappe.session.user
	if job_opening:
		filters["job_opening"] = job_opening
	shares = frappe.get_all(
		JOB_SHARE, filters=filters, fields=["name", "job_opening", "panelist", "panelist_name", "note", "last_shared_on", "shared_by"], order_by="last_shared_on desc"
	)
	if not manage:
		on_panel = set(frappe.get_all("Selection Committee", filters={"name": ["in", _my_committees() or [""]]}, pluck="job_opening"))
		shares = [s for s in shares if s.job_opening in on_panel]
	if not shares:
		return []
	labels = {}
	for r in frappe.get_all("Panel Shared Document", filters={"parenttype": JOB_SHARE, "parent": ["in", [s.name for s in shares]]}, fields=["parent", "document_label"], order_by="idx asc"):
		labels.setdefault(r.parent, []).append(r.document_label)
	jobs = {j.name: j for j in frappe.get_all("Job Opening", filters={"name": ["in", list({s.job_opening for s in shares})]}, fields=["name", "job_title", "position"])}
	rows = []
	for s in shares:
		job = jobs.get(s.job_opening) or frappe._dict()
		available = {f["label"]: f for f in job_files(s.job_opening)}
		rows.append(
			{
				"name": s.name, "job_opening": s.job_opening, "job_title": job.get("job_title") or s.job_opening, "position": job.get("position") or "",
				"panelist": s.panelist, "panelist_name": s.panelist_name or frappe.utils.get_fullname(s.panelist), "note": s.note or "",
				"shared_on": s.last_shared_on, "shared_by": frappe.utils.get_fullname(s.shared_by) if s.shared_by else "",
				"files": [{"label": label, "kind": available[label]["kind"]} for label in labels.get(s.name, []) if label in available],
			}
		)
	return rows
