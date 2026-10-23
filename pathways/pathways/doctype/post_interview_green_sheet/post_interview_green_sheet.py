# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Post-Interview ("selection") Green Sheet: workflow steps 20, 24 and 25.

After the Selection Committee's outcomes are recorded, the recruiter raises
this sheet recommending the selected candidate(s) and a waitlist, with the
pay fixation (Permanent) or fee table (Consultant / Research) and the
annexures, and moves it through the configured approval chain
(pathways.utils.approval). An Approved sheet is what Offers require.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from pathways.utils.approval import freeze_steps, set_approval_chain_template
from pathways.utils.approval import record_approval_action as _record_approval_action

DOCTYPE = "Post-Interview Green Sheet"
# A job may have at most one sheet in these states at a time. An Approved
# sheet does not block another (e.g. a second selection for the same job).
OPEN_STATUSES = ("Under Approval", "Returned for Revision")


class PostInterviewGreenSheet(Document):
	def validate(self):
		# Also copies the track from the Job Opening — without it no
		# template could ever be matched.
		set_approval_chain_template(self, DOCTYPE)
		if self.job_opening:
			self.employment_type = frappe.db.get_value("Job Opening", self.job_opening, "employment_type")
		self.validate_recommended_application()
		self.validate_compensation_rows()
		self.recommended_candidate_name = candidate_name(self.recommended_application)
		self.waitlist_candidate_name = candidate_name(self.waitlist_application)
		if self.docstatus == 0:
			self.validate_single_open_sheet(include_drafts=True)

	def validate_recommended_application(self):
		if not self.recommended_application:
			return
		app_job_opening = frappe.db.get_value("Application", self.recommended_application, "job_opening")
		if app_job_opening != self.job_opening:
			frappe.throw(_("Recommended Application does not belong to this Job Opening."))

		if self.waitlist_application:
			if self.waitlist_application == self.recommended_application:
				frappe.throw(_("The waitlisted candidate must differ from the recommended candidate."))
			wl_job_opening = frappe.db.get_value("Application", self.waitlist_application, "job_opening")
			if wl_job_opening != self.job_opening:
				frappe.throw(_("Waitlist Application does not belong to this Job Opening."))

	def validate_compensation_rows(self):
		for row in self.get("compensation_table") or []:
			if not row.application:
				continue
			if frappe.db.get_value("Application", row.application, "job_opening") != self.job_opening:
				frappe.throw(_("Row {0}: Application {1} does not belong to this Job Opening.").format(row.idx, row.application))
			if not row.candidate_name:
				row.candidate_name = candidate_name(row.application)

	def validate_single_open_sheet(self, include_drafts):
		others = frappe.get_all(
			DOCTYPE,
			filters={"job_opening": self.job_opening, "name": ["!=", self.name or ""], "docstatus": ["<", 2]},
			fields=["name", "docstatus", "status"],
		)
		for other in others:
			if other.docstatus == 1 and other.status in OPEN_STATUSES:
				frappe.throw(
					_("Job Opening {0} already has a Selection Green Sheet in progress ({1}, {2}).").format(
						self.job_opening, other.name, _(other.status)
					)
				)
			if include_drafts and other.docstatus == 0:
				frappe.throw(
					_("Job Opening {0} already has a draft Selection Green Sheet ({1}).").format(self.job_opening, other.name)
				)

	def before_submit(self):
		# Serialise two submits for the same job, then re-check under the lock.
		frappe.db.get_value("Job Opening", self.job_opening, "name", for_update=True)
		self.validate_single_open_sheet(include_drafts=False)
		freeze_steps(self)

	def on_submit(self):
		from pathways.utils.approval import get_current_step, notify_approvers

		step = get_current_step(self)
		if step:
			notify_approvers(self, step)

	def on_cancel(self):
		# Changes to self are not persisted after on_cancel, hence db_set.
		self.db_set({"status": "Draft", "current_approval_level": 0})

	# ------------------------------------------------------------ printing
	# Called from the Jinja print formats, which cannot run queries of
	# their own when render-time execution is restricted.

	def get_note_paragraphs(self):
		text = (self.selection_note or "").replace("\r\n", "\n")
		return [p.strip() for p in text.split("\n\n") if p.strip()]

	def get_print_steps(self):
		"""Signatories in order (the frozen steps, or the template's for a
		draft), with who approved each step and when."""
		from pathways.utils.approval import describe_approver, get_steps

		steps = get_steps(self)
		if not steps and self.approval_chain_template:
			steps = sorted(frappe.get_doc("Approval Chain Template", self.approval_chain_template).steps, key=lambda s: s.sequence)
		approvals = {}
		for row in self.get("approval_log") or []:
			if row.action == "Approved":
				approvals[row.sequence] = row
		out = []
		for s in steps:
			row = approvals.get(s.sequence)
			out.append(
				frappe._dict(
					label=s.approver_label or describe_approver(s),
					approver_name=frappe.utils.get_fullname(row.approver) if row else "",
					acted_on=frappe.utils.formatdate(row.acted_on, "dd MMM yyyy") if row else "",
				)
			)
		return out

	def get_annexures(self):
		from pathways.api.post_green_sheet import ANNEXURES

		return [frappe._dict(label=label, url=self.get(field)) for field, label in ANNEXURES if self.get(field)]

	def get_long_date(self, fieldname):
		value = self.get(fieldname)
		return frappe.utils.getdate(value).strftime("%B %-d, %Y") if value else ""

	def get_panel_recommendation(self):
		"""Data for the "Panel Recommendation" print format (workflow step
		20): the consolidated final-interview scores of this job. Callable
		from Jinja; reading the sheet is the permission to print it."""
		return panel_recommendation(self.job_opening, self)


def candidate_name(application):
	if not application:
		return None
	candidate = frappe.db.get_value("Application", application, "candidate")
	return (candidate and frappe.db.get_value("Candidate", candidate, "full_name")) or None


def panel_recommendation(job_opening, sheet=None):
	"""Consolidated final-interview scores per candidate (best average
	first), the committee and the outcomes. Mirrors the totals of
	pathways.api.panel.get_consolidated without its viewer restriction."""
	committee = frappe.db.get_value("Selection Committee", {"job_opening": job_opening}, ["name", "scheduled_date"], as_dict=True)
	members = []
	if committee:
		members = frappe.get_all(
			"Committee Member Row",
			filters={"parent": committee.name, "parenttype": "Selection Committee"},
			fields=["member", "designation_label", "is_external_expert"],
			order_by="idx asc",
		)
		for m in members:
			m.full_name = frappe.utils.get_fullname(m.member)
	member_ids = [m.member for m in members]

	apps = frappe.get_all("Application", filters={"job_opening": job_opening}, pluck="name") or [""]
	interviews = frappe.get_all(
		"Interview",
		filters={"round_type": "Final", "status": ["!=", "Cancelled"], "application": ["in", apps]},
		fields=["name", "application", "candidate_name", "scheduled_datetime"],
		order_by="scheduled_datetime asc",
	)
	assessments = {}
	if interviews:
		for a in frappe.get_all(
			"Interview Assessment",
			filters={"interview": ["in", [iv.name for iv in interviews]]},
			fields=["interview", "panelist", "total_score", "max_score", "verdict"],
		):
			assessments.setdefault(a.interview, {})[a.panelist] = a
	outcomes = dict(
		frappe.get_all("Application", filters={"name": ["in", [iv.application for iv in interviews] or [""]]}, fields=["name", "selection_outcome"], as_list=True)
	)

	rows, max_total = [], 0
	for iv in interviews:
		by_panellist = assessments.get(iv.name, {})
		scored = [a for p, a in by_panellist.items() if not member_ids or p in member_ids]
		average = sum(flt(a.total_score) for a in scored) / len(scored) if scored else 0
		if scored:
			max_total = max(max_total, flt(scored[0].max_score))
		verdicts = {}
		for a in scored:
			if a.verdict:
				verdicts[a.verdict] = verdicts.get(a.verdict, 0) + 1
		rows.append(
			frappe._dict(
				application=iv.application,
				candidate_name=iv.candidate_name,
				interview_date=iv.scheduled_datetime.date() if iv.scheduled_datetime else None,
				scores=[flt(by_panellist[m].total_score) if m in by_panellist else None for m in member_ids],
				scored=len(scored),
				average=round(average, 2),
				verdicts=", ".join(f"{k}: {v}" for k, v in verdicts.items()),
				outcome=outcomes.get(iv.application) or "",
			)
		)
	rows.sort(key=lambda r: (r.scored == 0, -r.average))
	for rank, r in enumerate(rows, start=1):
		r.rank = rank if r.scored else None
		r.percent = round(r.average * 100 / max_total, 1) if max_total else 0

	dates = sorted({r.interview_date for r in rows if r.interview_date})
	job = frappe.db.get_value("Job Opening", job_opening, ["job_title", "position", "department", "vacancies"], as_dict=True) or {}
	return frappe._dict(
		job=job,
		members=members,
		rows=rows,
		max_total=max_total,
		interview_dates=dates,
		selected=[r for r in rows if r.outcome == "Selected"],
		waitlisted=[r for r in rows if r.outcome == "Waitlisted"],
		recommended_name=(sheet and sheet.recommended_candidate_name) or None,
		waitlist_name=(sheet and sheet.waitlist_candidate_name) or None,
	)


@frappe.whitelist()
def record_approval_action(green_sheet_name, action, remarks=None, channel="Digital"):
	return _record_approval_action(DOCTYPE, green_sheet_name, action, remarks, channel)
