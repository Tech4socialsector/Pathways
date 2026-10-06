# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Configurable approval chains.

Nothing about who approves what lives in code. An Approval Chain Template
(Master Setup > Approval Chains) lists ordered steps for a Recruitment
Track + document type (+ optional employment type); each step names either
a Role (anyone holding it may act) or a specific User. Behaviour switches
(override role, one-person-many-steps) live in Pathways Settings.

Lifecycle of an approvable document (docstatus 0 -> 1):
	draft      the matching template is re-resolved on every save, so a
	           template configured/deactivated later is picked up
	submit     the template's steps are copied onto the document
	           (`approval_steps`) — editing the template afterwards never
	           changes an approval already in progress
	act        record_approval_action walks the frozen steps by sequence
	           order (sequences need not be contiguous: 10, 20, 30 is fine)

An approvable doctype must have: job_opening, track, approval_chain_template,
current_approval_level, status (Draft/Under Approval/Approved/Returned for
Revision), approval_steps (Approval Chain Step) and approval_log (Green
Sheet Approval Log). Register it in APPROVABLE_DOCTYPES.
"""

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

APPROVABLE_DOCTYPES = ("Pre-Recruitment Green Sheet", "Post-Interview Green Sheet")
ACTIONS = ("Approved", "Returned for Revision")


# ---------------------------------------------------------------- settings


def _settings():
	return frappe.get_cached_doc("Pathways Settings")


def get_override_role():
	return _settings().get("approval_override_role") or None


def allows_same_approver_multiple_steps():
	return bool(cint(_settings().get("allow_same_approver_multiple_steps")))


# ---------------------------------------------------------- template lookup


def find_template(track, applies_to, employment_type=None):
	"""Active template for this track + document type. A template scoped to
	the job's employment type wins over the track-wide one (blank type)."""
	if not track:
		return None
	candidates = frappe.get_all(
		"Approval Chain Template",
		filters={"track": track, "applies_to": applies_to, "is_active": 1},
		fields=["name", "employment_type"],
	)
	exact = [t.name for t in candidates if employment_type and t.employment_type == employment_type]
	if exact:
		return exact[0]
	general = [t.name for t in candidates if not t.employment_type]
	return general[0] if general else None


def set_approval_chain_template(doc, applies_to):
	"""Keep a draft's track and template in step with its Job Opening.
	Submitted documents are left alone — their steps are frozen."""
	if doc.docstatus != 0:
		return
	employment_type = None
	if doc.get("job_opening"):
		job = frappe.db.get_value("Job Opening", doc.job_opening, ["track", "employment_type"], as_dict=True)
		if job:
			doc.track = job.track
			employment_type = job.employment_type
	doc.approval_chain_template = find_template(doc.track, applies_to, employment_type)


def freeze_steps(doc):
	"""before_submit: copy the template's steps onto the document and point
	it at the first step."""
	if not doc.approval_chain_template:
		frappe.throw(
			_(
				"No active Approval Chain Template matches this job's track and employment type. "
				"Configure one in Master Setup > Approval Chains before submitting."
			)
		)
	template = frappe.get_doc("Approval Chain Template", doc.approval_chain_template)
	doc.set("approval_steps", [])
	for step in sorted(template.steps, key=lambda s: s.sequence):
		doc.append(
			"approval_steps",
			{
				"sequence": step.sequence,
				"approver_type": step.approver_type or "Role",
				"approver_role": step.approver_role,
				"approver_user": step.approver_user,
				"approver_label": step.approver_label,
			},
		)
	doc.set("approval_log", [])
	doc.status = "Under Approval"
	doc.current_approval_level = doc.approval_steps[0].sequence


def reset_for_amendment(doc):
	"""Clear approval state on a document copied from a cancelled one."""
	doc.status = "Draft"
	doc.current_approval_level = 0
	doc.approval_chain_template = None
	doc.set("approval_steps", [])
	doc.set("approval_log", [])


# ------------------------------------------------------------------- steps


def get_steps(doc):
	"""The document's frozen steps; falls back to the live template only for
	documents submitted before steps were frozen."""
	steps = list(doc.get("approval_steps") or [])
	if not steps and doc.get("approval_chain_template"):
		steps = list(frappe.get_cached_doc("Approval Chain Template", doc.approval_chain_template).steps)
	return sorted(steps, key=lambda s: s.sequence)


def get_current_step(doc, steps=None):
	steps = steps if steps is not None else get_steps(doc)
	return next((s for s in steps if s.sequence == doc.current_approval_level), None)


def get_next_step(doc, steps=None):
	steps = steps if steps is not None else get_steps(doc)
	return next((s for s in steps if s.sequence > doc.current_approval_level), None)


def describe_approver(step):
	if (step.get("approver_type") or "Role") == "User":
		return frappe.utils.get_fullname(step.approver_user) if step.approver_user else ""
	return step.approver_role or ""


def matches_step(step, user, roles=None):
	"""Is `user` the approver this step names (ignoring overrides)?"""
	if (step.get("approver_type") or "Role") == "User":
		return bool(step.approver_user) and step.approver_user == user
	roles = roles if roles is not None else frappe.get_roles(user)
	return bool(step.approver_role) and step.approver_role in roles


def check_can_act(doc, user=None, steps=None):
	"""(allowed, is_override, reason). Single source of truth used by the
	action itself, the pending-approvals list and the UI buttons."""
	user = user or frappe.session.user
	if doc.docstatus != 1 or doc.status != "Under Approval":
		return False, False, _("This document is not awaiting approval.")

	step = get_current_step(doc, steps)
	if not step:
		return False, False, _("The current approval step could not be resolved.")

	roles = frappe.get_roles(user)
	is_named_approver = matches_step(step, user, roles)
	already_approved = not allows_same_approver_multiple_steps() and any(
		row.approver == user and row.action == "Approved" and not row.get("is_override")
		for row in (doc.get("approval_log") or [])
	)
	if is_named_approver and not already_approved:
		return True, False, None

	# Recording on someone's behalf is always flagged in the log.
	override_role = get_override_role()
	if override_role and override_role in roles:
		return True, True, None

	if is_named_approver:
		return (
			False,
			False,
			_("You approved an earlier step of this document; a different person must approve this step."),
		)
	return False, False, _("This step is awaiting {0}.").format(step.approver_label or describe_approver(step))


# ----------------------------------------------------------------- actions


def record_approval_action(doctype, docname, action, remarks=None, channel="Digital"):
	if doctype not in APPROVABLE_DOCTYPES:
		frappe.throw(_("Approval actions are not supported for {0}.").format(doctype))
	if action not in ACTIONS:
		frappe.throw(_("Invalid action."))
	if channel not in ("Digital", "Email", "Signature"):
		frappe.throw(_("Invalid channel."))
	if action == "Returned for Revision" and not (remarks or "").strip():
		frappe.throw(_("Please give a reason when returning a document for revision."))

	# Row lock: two approvers clicking at the same moment must not both
	# act on the same step.
	doc = frappe.get_doc(doctype, docname, for_update=True)
	steps = get_steps(doc)
	allowed, is_override, reason = check_can_act(doc, steps=steps)
	if not allowed:
		frappe.throw(reason, frappe.PermissionError)

	step = get_current_step(doc, steps)
	doc.append(
		"approval_log",
		{
			"sequence": step.sequence,
			"approver": frappe.session.user,
			"approver_role": step.approver_label or describe_approver(step),
			"action": action,
			"channel": channel,
			"remarks": remarks,
			"acted_on": now_datetime(),
			"is_override": 1 if is_override else 0,
		},
	)

	next_step = None
	if action == "Returned for Revision":
		doc.status = "Returned for Revision"
		doc.current_approval_level = 0
	else:
		next_step = get_next_step(doc, steps)
		if next_step:
			doc.current_approval_level = next_step.sequence
		else:
			doc.status = "Approved"

	doc.save(ignore_permissions=True)

	if next_step:
		notify_approvers(doc, next_step)
	elif doc.owner and doc.owner != frappe.session.user:
		_notify(
			[doc.owner],
			doc,
			_("{0} {1} was {2}").format(_(doctype), doc.name, _(doc.status.lower())),
		)
	return doc.status


# -------------------------------------------------------------- reporting


def get_pending_for_user(user=None):
	"""Documents currently sitting at a step this user may act on."""
	user = user or frappe.session.user
	pending = []
	for doctype in APPROVABLE_DOCTYPES:
		for name in frappe.get_all(doctype, filters={"status": "Under Approval", "docstatus": 1}, pluck="name"):
			doc = frappe.get_doc(doctype, name)
			steps = get_steps(doc)
			allowed, is_override, _reason = check_can_act(doc, user, steps)
			if not allowed:
				continue
			step = get_current_step(doc, steps)
			pending.append(
				{
					"doctype": doctype,
					"name": doc.name,
					"job_opening": doc.job_opening,
					"job_title": frappe.db.get_value("Job Opening", doc.job_opening, "job_title"),
					"approver_label": step.approver_label or describe_approver(step),
					"is_override": is_override,
					"submitted_on": doc.modified,
				}
			)
	return pending


def is_approver(user=None):
	"""Does this user appear in any approval chain (template or in-flight)?
	Drives the "My Approvals" menu instead of a hardcoded role list."""
	user = user or frappe.session.user
	roles = frappe.get_roles(user)
	override_role = get_override_role()
	if override_role and override_role in roles:
		return True
	if frappe.db.exists("Approval Chain Step", {"approver_type": "User", "approver_user": user}):
		return True
	return bool(
		frappe.db.exists(
			"Approval Chain Step",
			{"approver_type": ["!=", "User"], "approver_role": ["in", roles]},
		)
	)


def get_chain_status(doc):
	steps = get_steps(doc)
	approved_sequences = {row.sequence for row in (doc.get("approval_log") or []) if row.action == "Approved"}
	return {
		"steps": [
			{
				"sequence": s.sequence,
				"approver_type": s.get("approver_type") or "Role",
				"approver_role": describe_approver(s),
				"approver_label": s.approver_label,
				"completed": s.sequence in approved_sequences,
			}
			for s in steps
		],
		"current_level": doc.current_approval_level,
		"status": doc.status,
		"log": [
			{
				"sequence": row.sequence,
				"approver": row.approver,
				"approver_name": frappe.utils.get_fullname(row.approver) if row.approver else None,
				"approver_role": row.approver_role,
				"action": row.action,
				"channel": row.channel,
				"remarks": row.remarks,
				"acted_on": row.acted_on,
				"is_override": row.get("is_override"),
			}
			for row in (doc.get("approval_log") or [])
		],
	}


# ----------------------------------------------------------- notification


def get_step_users(step):
	if (step.get("approver_type") or "Role") == "User":
		return [step.approver_user] if step.approver_user else []
	if not step.approver_role:
		return []
	return frappe.get_all(
		"User",
		filters=[["Has Role", "role", "=", step.approver_role], ["enabled", "=", 1], ["name", "not in", ("Administrator", "Guest")]],
		pluck="name",
		distinct=True,
	)


def notify_approvers(doc, step):
	_notify(
		get_step_users(step),
		doc,
		_("{0} {1} is awaiting your approval ({2})").format(_(doc.doctype), doc.name, step.approver_label or ""),
	)


def _notify(users, doc, subject):
	"""Bell notification (Notification Log). Never blocks the approval."""
	users = [u for u in set(users) if u and u != frappe.session.user]
	if not users:
		return
	try:
		from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

		enqueue_create_notification(
			users,
			{
				"type": "Alert",
				"document_type": doc.doctype,
				"document_name": doc.name,
				"subject": subject,
				"from_user": frappe.session.user,
			},
		)
	except Exception:
		frappe.log_error(title=f"Pathways approval notification failed for {doc.doctype} {doc.name}")
