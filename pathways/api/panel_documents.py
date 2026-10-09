# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Documents page > Share with panel: the recruitment team chooses which of
the candidates' documents each Selection Committee panellist should read.
Shares are recorded per application and panellist (Panel Document Share),
each panellist gets one email with a link, and reads them on Interview
Panel > Shared documents. Files are never attached to the email."""

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
	if not shares:
		return {"rows": [], "can_manage": 1 if manage else 0}

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
	return {"rows": rows, "can_manage": 1 if manage else 0}


def shared_for_panelist(application, panelist):
	"""The documents of `application` shared with `panelist`, resolved to
	the current files, for the Interview Assessment Form."""
	labels = _shared_labels([application], [panelist]).get((application, panelist))
	if not labels:
		return []
	return [d for d in _application_documents(frappe.get_doc("Application", application)) if d["label"] in labels]
