# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Master Setup registry and the integrity guards that apply to it.

Master Setup is an access layer over EXISTING master DocTypes — it never
owns data of its own. Every master shown on the /pathways/master-setup
page, and every guard below, is driven by MASTER_SETUP. To add a master,
append one entry to the right category; nothing else needs to change.

Entry keys:
	doctype       (required) existing DocType to surface
	label         plural card title
	singular      used in "Add <singular>" / error messages (default: doctype)
	description   one-line card description
	icon          feather icon name
	keywords      extra search terms for the landing-page search
	unique_fields fields that together must be unique — only needed for
	              hash-named masters; field-named masters are already
	              unique through their primary key.

Access is permission-driven, not role-driven: a master is visible to a
user only if their role permissions grant write/create on its DocType
(System Manager / Pathways Admin today; configurable per master through
Role Permission Manager). Read-only users of a master — e.g. Recruiters,
who need it for Link fields — therefore do not get Master Setup.
"""

import frappe
from frappe import _

MASTER_SETUP = [
	{
		"key": "organisation",
		"label": "Organisation",
		"masters": [
			{
				"doctype": "Department",
				"label": "Departments",
				"description": "Manage university departments.",
				"icon": "layers",
				"keywords": ["centre", "school", "unit", "office"],
			},
			{
				"doctype": "Designation",
				"label": "Designations",
				"description": "Manage job designations and positions.",
				"icon": "user",
				"keywords": ["position", "post", "role", "pay level", "employment type"],
			},
		],
	},
	{
		"key": "recruitment",
		"label": "Recruitment",
		"masters": [
			{
				"doctype": "Recruitment Track",
				"label": "Recruitment Tracks",
				"singular": "Recruitment Track",
				"description": "Manage recruitment tracks such as Faculty, Staff and Research.",
				"icon": "git-branch",
				"keywords": ["job category", "category", "teaching", "non-teaching", "faculty", "staff"],
			},
			{
				"doctype": "Candidate Source",
				"label": "Recruitment Sources",
				"singular": "Candidate Source",
				"description": "Manage candidate and application sources.",
				"icon": "share-2",
				"keywords": ["candidate source", "referral", "channel", "advertisement"],
			},
			{
				"doctype": "Approval Chain Template",
				"label": "Approval Chains",
				"singular": "Approval Chain Template",
				"description": "Manage green sheet approval sequences per track.",
				"icon": "list",
				"keywords": ["approval", "green sheet", "workflow", "approver"],
			},
		],
	},
	{
		"key": "interview_selection",
		"label": "Interview & Selection",
		"masters": [
			{
				"doctype": "Scoring Rubric Template",
				"label": "Scoring Rubrics",
				"singular": "Scoring Rubric Template",
				"description": "Manage shortlisting and interview scoring criteria.",
				"icon": "clipboard",
				"keywords": ["interview", "shortlisting", "selection", "stage", "round", "criteria", "score"],
			},
		],
	},
	{
		"key": "candidate_documents",
		"label": "Candidate & Documents",
		"masters": [
			{
				"doctype": "Document Type Master",
				"label": "Document Types",
				"singular": "Document Type",
				"description": "Manage documents required from candidates.",
				"icon": "file",
				"keywords": ["document", "onboarding", "upload", "attachment"],
			},
			{
				"doctype": "Institution Master",
				"label": "Institutions",
				"singular": "Institution",
				"description": "Manage institutions used in candidate qualifications.",
				"icon": "book-open",
				"keywords": ["university", "college", "qualification", "education"],
				"unique_fields": ["institution_name", "list_type"],
			},
			{
				"doctype": "Specialization Master",
				"label": "Specialisations",
				"singular": "Specialisation",
				"description": "Manage subject specialisations by discipline.",
				"icon": "bookmark",
				"keywords": ["specialization", "discipline", "subject", "qualification"],
				"unique_fields": ["specialization_name", "discipline"],
			},
			{
				"doctype": "UGC NET Subject Master",
				"label": "UGC NET Subjects",
				"singular": "UGC NET Subject",
				"description": "Manage UGC NET subjects.",
				"icon": "book",
				"keywords": ["net", "jrf", "eligibility", "qualification"],
			},
		],
	},
]

# Link fields that must not be pointed at an inactive master when they are
# set or changed. Deliberately an explicit list: fields copied from an
# upstream record (e.g. Employee.department from its Job Opening) are left
# out so an in-flight recruitment never breaks when a master is retired.
INACTIVE_LINK_GUARDS = {
	"Job Opening": ["track", "department", "designation"],
	"Application": ["source"],
	"Department": ["parent_department"],
	"Designation": ["track"],
	"Document Type Master": ["track"],
	"Scoring Rubric Template": ["track"],
	"Approval Chain Template": ["track"],
}


def get_master(doctype):
	for category in MASTER_SETUP:
		for master in category["masters"]:
			if master["doctype"] == doctype:
				return master
	return None


def get_active_field(meta):
	"""(fieldname, value-meaning-active) for whichever activation flag the
	DocType already has — reused as-is, never added."""
	for fieldname, active_value in (("is_active", 1), ("enabled", 1), ("disabled", 0)):
		if meta.has_field(fieldname):
			return fieldname, active_value
	return None, None


def can_manage(doctype):
	if not frappe.db.exists("DocType", doctype):
		return False
	return frappe.has_permission(doctype, "write") or frappe.has_permission(doctype, "create")


def _singular(master):
	return master.get("singular") or master["doctype"]


def _skip_guards():
	flags = frappe.flags
	return flags.in_install or flags.in_uninstall or flags.in_migrate or flags.in_patch or flags.in_import


def validate(doc, method=None):
	"""doc_events["*"]["validate"] — cheap dict lookups for unrelated DocTypes."""
	if _skip_guards():
		return
	_prevent_duplicate_master(doc)
	_prevent_inactive_references(doc)


def _prevent_duplicate_master(doc):
	master = get_master(doc.doctype)
	if not master or not master.get("unique_fields"):
		return

	filters = {f: (doc.get(f) or "").strip() for f in master["unique_fields"]}
	filters["name"] = ["!=", doc.name]
	if frappe.db.exists(doc.doctype, filters):
		labels = ", ".join(_(doc.meta.get_label(f)) for f in master["unique_fields"])
		frappe.throw(
			_("This {0} already exists (same {1}).").format(_(_singular(master)), labels),
			frappe.DuplicateEntryError,
			title=_("Duplicate Record"),
		)


def _prevent_inactive_references(doc):
	fieldnames = INACTIVE_LINK_GUARDS.get(doc.doctype)
	if not fieldnames:
		return

	before = doc.get_doc_before_save()
	for fieldname in fieldnames:
		value = doc.get(fieldname)
		if not value or (before and before.get(fieldname) == value):
			continue

		df = doc.meta.get_field(fieldname)
		if not df or df.fieldtype != "Link":
			continue

		active_field, active_value = get_active_field(frappe.get_meta(df.options))
		if not active_field:
			continue

		if frappe.db.get_value(df.options, value, active_field) != active_value:
			frappe.throw(
				_("{0} '{1}' is inactive and cannot be used. Choose an active {0} or reactivate it in Master Setup.").format(
					_(df.options), value
				),
				title=_("Inactive {0}").format(_(df.options)),
			)


def on_trash(doc, method=None):
	"""doc_events["*"]["on_trash"] — runs before Frappe's own link check, so
	in-use masters get an actionable message instead of the generic
	"linked with" error. Frappe's check still runs afterwards regardless."""
	if _skip_guards():
		return

	master = get_master(doc.doctype)
	if not master:
		return

	from frappe.model.delete_doc import get_linked_docs

	links = get_linked_docs(doc)
	if not links:
		return

	first = links[0]
	example = f"{_(first['reference_doctype'])} {first['reference_docname']}"
	message = _("This {0} is currently used by existing recruitment records (for example, {1}) and cannot be deleted.").format(
		_(_singular(master)), example
	)
	if get_active_field(doc.meta)[0]:
		message += " " + _("You can deactivate it instead.")

	frappe.throw(message, frappe.LinkExistsError, title=_("Cannot Delete"))
