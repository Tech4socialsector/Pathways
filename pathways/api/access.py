# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Roles & Permissions.

Two halves:

* get_my_access — what the session user may see/do, computed from Role
  Permissions; the SPA builds its menu and buttons from this instead of
  hardcoded role names.
* The System Manager endpoints behind Pathways > Roles & Permissions:
  manage which roles belong to Pathways, which users hold them, and what
  each role may do on every Pathways DocType. Permissions are stored as
  standard Frappe Custom DocPerm rows — exactly what Desk's Role
  Permission Manager writes — so both screens always agree.
"""

import frappe
from frappe import _
from frappe.permissions import setup_custom_perms
from frappe.utils import cint, validate_email_address

from pathways.permissions import (
	CANDIDATE_ROLE,
	SCOPED_ROLES,
	SELECTION_ROLE,
	SHORTLISTING_ROLE,
	TAGGED_ROLE,
	get_pathways_roles,
	has_full_access,
)
from pathways.utils.approval import is_approver
from pathways.utils.master_setup import MASTER_SETUP, can_manage

MANAGER_ROLE = "System Manager"
ADMIN_ROLE = "Pathways Admin"
# Roles & Permissions is open to both. A Pathways Admin works only inside
# Pathways (its roles and DocTypes) and cannot raise its own reach: it cannot
# bring an existing non-Pathways role in, change or drop the Pathways Admin
# role, or take that role from themselves.
ACCESS_ROLES = (MANAGER_ROLE, ADMIN_ROLE)
PTYPES = ("read", "write", "create", "delete", "submit", "cancel", "amend")
SUBMIT_PTYPES = ("submit", "cancel", "amend")
# Turning a permission on turns on what it needs; turning one off turns
# off what depends on it (mirrors Frappe's own validation rules).
REQUIRES = {
	"write": ("read",),
	"create": ("read",),
	"delete": ("read",),
	"submit": ("write",),
	"cancel": ("submit",),
	"amend": ("cancel",),
}
PROTECTED_ROLES = {"Administrator", "Guest", "All", "Desk User", MANAGER_ROLE}

# Sidebar entries and the DocType permission that reveals each one. The
# Roles & Permissions screen shows this mapping, so granting "read" on a
# DocType visibly grants the menu.
MENU_ITEMS = (
	{"key": "jobs", "label": "Job Openings", "doctype": "Job Opening"},
	{"key": "candidates", "label": "Candidate Master", "doctype": "Candidate"},
	{"key": "applications", "label": "Applications", "doctype": "Application"},
	{"key": "interviews", "label": "Interviews", "doctype": "Interview"},
	{"key": "offers", "label": "Offers", "doctype": "Offer Appointment Order"},
	{"key": "documents", "label": "Documents", "doctype": "Document Collection"},
	{"key": "joinings", "label": "Joinings", "doctype": "Joining"},
	{"key": "it_requests", "label": "IT Requests", "doctype": "IT Facilities Provisioning Request"},
	{"key": "honorarium", "label": "Panel Honorarium", "doctype": "Panel Honorarium"},
	{"key": "communications", "label": "Communications", "doctype": "Communication Log"},
)


# ------------------------------------------------------------- my access


def _doctype_perms(doctype, user=None):
	return {ptype: bool(frappe.has_permission(doctype, ptype, user=user)) for ptype in PTYPES}


@frappe.whitelist()
def get_my_access():
	"""Everything the SPA needs to decide what to show this user."""
	user = frappe.session.user
	if user == "Guest":
		return {"user": None, "is_staff": False, "is_candidate": False}
	from pathways.utils.candidate_account import must_change_password

	all_roles = set(frappe.get_roles(user))
	pathways_roles = get_pathways_roles()
	is_system_user = frappe.db.get_value("User", user, "user_type") == "System User"
	# Administrator holds every role; never treat a System User as a candidate.
	roles = sorted(r for r in all_roles if r in pathways_roles or r == MANAGER_ROLE)
	if is_system_user:
		roles = [r for r in roles if r != CANDIDATE_ROLE]
	is_staff = is_system_user and bool(roles)

	menu = []
	doctypes = {}
	if is_staff:
		for item in MENU_ITEMS:
			perms = _doctype_perms(item["doctype"])
			doctypes[item["doctype"]] = perms
			if perms["read"]:
				menu.append(item["key"])
		for doctype in ("Pre-Recruitment Green Sheet", "Post-Interview Green Sheet", "Pathways Settings"):
			doctypes[doctype] = _doctype_perms(doctype)
		if is_approver(user):
			menu.append("approvals")
		# Interview Panel: Selection Committee members score final interviews.
		# HR assessors of Round 1 interviews fill their sheet there too.
		if frappe.db.exists("Selection Committee", [["Committee Member Row", "member", "=", user]]) or frappe.db.exists(
			"Interview HR Assessor", {"assessor": user, "parenttype": "Interview"}
		) or (
			"interviews" in menu and doctypes.get("Interview", {}).get("create")
		):
			menu.append("panel")
		# Selection: the recruitment team's post-interview steps (decisions,
		# regrets and thanks, selection green sheet, offers).
		from pathways.api.interviews import _can_manage

		if _can_manage():
			menu.append("selection")
		pipeline = has_full_access("Application")
		if pipeline:
			menu.append("reports")
		if any(can_manage(m["doctype"]) for category in MASTER_SETUP for m in category["masters"]):
			menu.append("master_setup")
	else:
		pipeline = False

	profile = frappe.db.get_value("User", user, ["full_name", "user_image"], as_dict=True) or {}
	return {
		"user": user,
		"full_name": profile.get("full_name") or user,
		"user_image": profile.get("user_image"),
		"roles": roles,
		"is_staff": is_staff,
		"is_candidate": not is_system_user and CANDIDATE_ROLE in all_roles,
		"must_change_password": (not is_system_user) and must_change_password(user),
		"menu": menu,
		"doctypes": doctypes,
		"can_view_pipeline": pipeline,
		"can_manage_access": bool(all_roles & set(ACCESS_ROLES)),
		"can_manage_settings": bool(doctypes.get("Pathways Settings", {}).get("write")),
	}


# ------------------------------------------------------ System Manager API


def _only_manager():
	frappe.only_for(ACCESS_ROLES)


def _is_system_manager():
	return MANAGER_ROLE in frappe.get_roles()


def _guard_admin_role(role, action):
	"""Only a System Manager may change the Pathways Admin role itself."""
	if role == ADMIN_ROLE and not _is_system_manager():
		frappe.throw(_("Only a System Manager can {0} the {1} role.").format(action, ADMIN_ROLE), frappe.PermissionError)


def _save_user_roles(user, add=(), remove=()):
	"""Change a user's Pathways roles. The endpoints check who may do it;
	the User record itself is writable only by System Managers in Desk."""
	doc = frappe.get_doc("User", user)
	doc.flags.ignore_permissions = True
	if add:
		doc.add_roles(*add)
	if remove:
		doc.remove_roles(*remove)


def _pathways_doctypes():
	"""Every non-child Pathways DocType, i.e. everything a role can be
	granted access to in this app."""
	return frappe.get_all(
		"DocType",
		filters={"module": "Pathways", "istable": 0},
		fields=["name", "is_submittable", "issingle"],
		order_by="name asc",
	)


def _assert_doctype(doctype):
	if not frappe.db.exists("DocType", {"name": doctype, "module": "Pathways", "istable": 0}):
		frappe.throw(_("{0} is not a Pathways document type.").format(doctype))


def _assert_editable_role(role):
	if role not in get_pathways_roles():
		frappe.throw(_("{0} is not a Pathways role.").format(role))
	if role == CANDIDATE_ROLE:
		frappe.throw(
			_("Candidate permissions are fixed: candidates only ever reach their own records through the portal.")
		)


def _role_rows(doctype):
	"""Level-0 permission rows by role, as currently in force (Custom
	DocPerm if the DocType has any, else the standard DocPerm)."""
	rows = {}
	for perm in frappe.get_meta(doctype).permissions:
		if perm.permlevel:
			continue
		entry = rows.setdefault(perm.role, {ptype: 0 for ptype in PTYPES} | {"if_owner": 0})
		for ptype in PTYPES:
			entry[ptype] = entry[ptype] or cint(perm.get(ptype))
		entry["if_owner"] = entry["if_owner"] or cint(perm.if_owner)
	return rows


def _user_counts(roles):
	if not roles:
		return {}
	rows = frappe.db.sql(
		"""select hr.role, count(distinct hr.parent)
		from `tabHas Role` hr join `tabUser` u on u.name = hr.parent
		where hr.parenttype = 'User' and u.enabled = 1
			and u.name not in ('Administrator', 'Guest') and hr.role in %(roles)s
		group by hr.role""",
		{"roles": list(roles)},
	)
	return dict(rows)


@frappe.whitelist()
def get_access_matrix():
	_only_manager()
	roles = sorted(get_pathways_roles())
	counts = _user_counts(roles)
	doctypes = _pathways_doctypes()
	menu_by_doctype = {}
	for item in MENU_ITEMS:
		menu_by_doctype.setdefault(item["doctype"], []).append(item["label"])

	is_manager = _is_system_manager()
	matrix = {role: {} for role in roles}
	customised = []
	for dt in doctypes:
		rows = _role_rows(dt.name)
		if frappe.db.exists("Custom DocPerm", {"parent": dt.name}):
			customised.append(dt.name)
		for role in roles:
			if role in rows:
				matrix[role][dt.name] = rows[role]

	return {
		"roles": [
			{
				"role": role,
				"users": counts.get(role, 0),
				"editable": role != CANDIDATE_ROLE,
				# Pathways Admin's own grants and the role itself: System Manager only.
				"system_manager_only": role == ADMIN_ROLE and not is_manager,
				"row_scoped": role in SCOPED_ROLES,
				"desk_access": cint(frappe.db.get_value("Role", role, "desk_access")),
			}
			for role in roles
		],
		"doctypes": [
			{
				"name": dt.name,
				"is_submittable": cint(dt.is_submittable),
				"is_single": cint(dt.issingle),
				"menus": menu_by_doctype.get(dt.name, []),
				"customised": dt.name in customised,
			}
			for dt in doctypes
		],
		"ptypes": list(PTYPES),
		"matrix": matrix,
	}


def _resolve(current, ptype, value, allowed):
	"""Apply one toggle plus its dependencies to a {ptype: 0/1} dict."""
	perms = {p: cint(current.get(p)) for p in PTYPES}
	if value:
		stack = [ptype]
		while stack:
			p = stack.pop()
			if p in allowed and not perms[p]:
				perms[p] = 1
				stack.extend(REQUIRES.get(p, ()))
			elif p in allowed:
				stack.extend(REQUIRES.get(p, ()))
	else:
		stack = [ptype]
		while stack:
			p = stack.pop()
			perms[p] = 0
			stack.extend(child for child, needs in REQUIRES.items() if p in needs and perms[child])
	for p in PTYPES:
		if p not in allowed:
			perms[p] = 0
	return perms


@frappe.whitelist(methods=["POST"])
def set_role_permission(doctype, role, ptype, value):
	"""Toggle one permission for a role on a DocType (with dependencies)."""
	_only_manager()
	_assert_doctype(doctype)
	_assert_editable_role(role)
	_guard_admin_role(role, _("change the permissions of"))
	if ptype not in PTYPES:
		frappe.throw(_("Unknown permission type {0}.").format(ptype))

	meta = frappe.get_meta(doctype)
	allowed = set(PTYPES)
	if not meta.is_submittable:
		allowed -= set(SUBMIT_PTYPES)
	if meta.issingle:
		allowed -= {"create", "delete"}
	if ptype not in allowed:
		frappe.throw(_("{0} does not support the {1} permission.").format(doctype, _(ptype.title())))

	setup_custom_perms(doctype)
	name = frappe.db.get_value(
		"Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0}, "name"
	)
	current = frappe.db.get_value("Custom DocPerm", name, list(PTYPES), as_dict=True) if name else {}
	perms = _resolve(current or {}, ptype, cint(value), allowed)

	if not any(perms.values()):
		if name:
			frappe.delete_doc("Custom DocPerm", name, ignore_permissions=True)
	else:
		row = (
			frappe.get_doc("Custom DocPerm", name)
			if name
			else frappe.get_doc(
				{
					"doctype": "Custom DocPerm",
					"parent": doctype,
					"parenttype": "DocType",
					"parentfield": "permissions",
					"role": role,
					"permlevel": 0,
					"if_owner": 0,
				}
			)
		)
		row.update(perms)
		if perms["read"] and not name:
			# Sensible companions for a brand-new grant.
			row.update({"print": 1, "report": 1})
		row.save(ignore_permissions=True)

	frappe.clear_cache(doctype=doctype)
	return {"doctype": doctype, "role": role, "perms": perms}


@frappe.whitelist(methods=["POST"])
def reset_doctype_permissions(doctype):
	"""Drop customisations and go back to the permissions shipped with the app."""
	_only_manager()
	_assert_doctype(doctype)
	from frappe.permissions import reset_perms

	reset_perms(doctype)
	frappe.clear_cache(doctype=doctype)
	return True


# ------------------------------------------------------------------ roles


def _settings_for_update():
	settings = frappe.get_single("Pathways Settings")
	settings.flags.ignore_mandatory = True
	return settings


@frappe.whitelist(methods=["POST"])
def create_role(role_name, desk_access=1):
	"""Create a role (or adopt an existing one) and add it to Pathways."""
	_only_manager()
	role_name = (role_name or "").strip()
	if not role_name:
		frappe.throw(_("Role name is required."))
	if role_name in PROTECTED_ROLES:
		frappe.throw(_("{0} cannot be managed from Pathways.").format(role_name))
	exists = frappe.db.exists("Role", role_name)
	if exists and role_name not in get_pathways_roles() and not _is_system_manager():
		# It may give access to other apps (SLCM, ERPNext...).
		frappe.throw(
			_("{0} already exists outside Pathways. Only a System Manager can add it to Pathways; choose another name.").format(role_name),
			frappe.PermissionError,
		)

	if not exists:
		frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": cint(desk_access)}).insert(ignore_permissions=True)

	if role_name not in get_pathways_roles():
		settings = _settings_for_update()
		settings.append("pathways_roles", {"role": role_name})
		settings.save()
	return role_name


@frappe.whitelist(methods=["POST"])
def remove_role(role):
	"""Remove a role from Pathways (the Role itself and its grants stay, so
	this is reversible). Built-in behavioural roles cannot be removed."""
	_only_manager()
	if role in SCOPED_ROLES:
		frappe.throw(_("{0} is used by the application itself and cannot be removed.").format(role))
	_guard_admin_role(role, _("remove"))
	settings = _settings_for_update()
	settings.set("pathways_roles", [row for row in settings.pathways_roles if row.role != role])
	settings.save()
	return True


# ------------------------------------------------------------------ users


@frappe.whitelist()
def get_role_users(role):
	_only_manager()
	if role not in get_pathways_roles():
		frappe.throw(_("{0} is not a Pathways role.").format(role))
	return frappe.get_all(
		"User",
		filters=[["Has Role", "role", "=", role], ["name", "not in", ["Administrator", "Guest"]]],
		fields=["name", "full_name", "user_type", "enabled", "last_active"],
		order_by="full_name asc",
		distinct=True,
	)


@frappe.whitelist()
def search_users(txt=""):
	_only_manager()
	txt = (txt or "").strip()
	filters = [["name", "not in", ["Administrator", "Guest"]], ["enabled", "=", 1]]
	or_filters = [["name", "like", f"%{txt}%"], ["full_name", "like", f"%{txt}%"]] if txt else None
	return frappe.get_all(
		"User",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "full_name", "user_type"],
		order_by="full_name asc",
		limit_page_length=20,
	)


@frappe.whitelist(methods=["POST"])
def assign_role(user, role):
	_only_manager()
	if role not in get_pathways_roles():
		frappe.throw(_("{0} is not a Pathways role.").format(role))
	if user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
		frappe.throw(_("Choose a valid user."))
	_save_user_roles(user, add=[role])
	return True


@frappe.whitelist(methods=["POST"])
def unassign_role(user, role):
	_only_manager()
	if role not in get_pathways_roles():
		frappe.throw(_("{0} is not a Pathways role.").format(role))
	if user in ("Administrator", "Guest") or not frappe.db.exists("User", user):
		frappe.throw(_("Choose a valid user."))
	if role == ADMIN_ROLE and user == frappe.session.user and not _is_system_manager():
		frappe.throw(_("You cannot remove the {0} role from yourself. Ask another administrator.").format(ADMIN_ROLE))
	_save_user_roles(user, remove=[role])
	return True


@frappe.whitelist(methods=["POST"])
def create_staff_user(email, first_name, last_name=None, roles=None):
	"""Create a staff (System) user, email them a set-password link and give
	them Pathways roles in one step."""
	_only_manager()
	email = (email or "").strip().lower()
	if not validate_email_address(email):
		frappe.throw(_("Enter a valid email address."))
	if frappe.db.exists("User", email):
		frappe.throw(_("A user with this email already exists — assign roles to them instead."))
	if isinstance(roles, str):
		roles = frappe.parse_json(roles)
	roles = [r for r in (roles or []) if r in get_pathways_roles() and r != CANDIDATE_ROLE]

	# Pathways' own welcome (Email Setup > Staff & Access) explains the roles;
	# Frappe's generic one is the fallback when that email is turned off.
	own_welcome = bool(frappe.db.get_value("Recruitment Email Rule", WELCOME_EVENT, "enabled"))
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": (first_name or "").strip() or email,
			"last_name": (last_name or "").strip() or None,
			"user_type": "System User",
			"send_welcome_email": 0 if own_welcome else 1,
		}
	)
	user.insert(ignore_permissions=True)
	if roles:
		_save_user_roles(user.name, add=roles)
		user.reload()
	if own_welcome:
		send_staff_welcome(user)
	return user.name


# ------------------------------------------------------------- welcome email

WELCOME_EVENT = "staff_welcome"

# What each standard role is for, in plain words. A role added later from
# this screen gets a summary built from the sections it opens.
ROLE_SUMMARY = {
	"Pathways Admin": "Runs Pathways end to end: job openings, applications, interviews, offers, onboarding and the master setup. "
	"Can also step in on an approval when the approver is away.",
	"Pathways Recruiter": "Manages recruitment day to day: creates job openings and green sheets, screens applications, "
	"schedules interviews and sends the candidate emails.",
	"Pathways PNCO": "People and Culture Office: reviews green sheets, verifies new joiners' documents and supports offers and joining.",
	"Pathways Director People Culture": "Oversees People and Culture recruitment and approves green sheets when they reach your step.",
	"Pathways Dean Academics": "Approves faculty recruitment green sheets when they reach your step.",
	"Pathways Dean Research": "Approves research recruitment green sheets when they reach your step.",
	"Pathways Senior Manager Research": "Raises and approves research recruitment green sheets.",
	"Pathways CFO": "Reviews the budget side of recruitment: approves green sheets when they reach your step and panel honorarium.",
	"Pathways Registrar": "Approves green sheets, signs corrigenda and appointment orders.",
	"Pathways Vice Chancellor": "Gives the final approval on recruitment green sheets.",
	SHORTLISTING_ROLE: "Scores and shortlists applications for the jobs whose Shortlisting Committee you are on. You see only those jobs.",
	SELECTION_ROLE: "Interviews and scores candidates for the jobs whose Selection Committee you are on, and the Round 1 interviews "
	"you are asked to assess, from the Interview Panel page.",
	"Pathways Communications": "Publishes job notifications and advertisements, and takes them down when a job closes.",
	"Pathways IT Facilities": "Sets up a new joiner's laptop, NLS email ID, access card and seating from the IT Requests page.",
	TAGGED_ROLE: "Reads the applications and documents of the jobs you are tagged on (\"Shared with\").",
}


def role_guide(roles):
	"""[{title, summary, sections, approvals}] for the welcome email: what
	each Pathways role is for, the sidebar sections its permissions open
	and the approval steps it takes."""
	pathways_roles = get_pathways_roles()
	roles = sorted(r for r in roles or [] if r in pathways_roles and r != CANDIDATE_ROLE)
	perms = {item["doctype"]: _role_rows(item["doctype"]) for item in MENU_ITEMS}
	chains = frappe.get_all(
		"Approval Chain Template", filters={"is_active": 1}, fields=["name", "template_name", "applies_to", "track"], order_by="track asc, applies_to desc"
	)
	steps = frappe.get_all(
		"Approval Chain Step",
		filters={"parenttype": "Approval Chain Template", "parent": ["in", [c.name for c in chains] or [""]]},
		fields=["parent", "sequence", "approver_type", "approver_role", "approver_label"],
	)
	guide = []
	for role in roles:
		sections = [item["label"] for item in MENU_ITEMS if perms[item["doctype"]].get(role, {}).get("read")]
		if role == SELECTION_ROLE:
			sections.append(_("Interview Panel"))
		approvals = []
		for chain in chains:
			chain_steps = sorted((s for s in steps if s.parent == chain.name), key=lambda s: cint(s.sequence))
			for i, step in enumerate(chain_steps, start=1):
				if step.approver_type == "Role" and step.approver_role == role:
					approvals.append(
						_("{0} ({1} track), step {2} of {3}{4}").format(
							_(chain.applies_to), chain.track or _("any"), i, len(chain_steps), f" as {step.approver_label}" if step.approver_label else ""
						)
					)
		summary = ROLE_SUMMARY.get(role) or (
			_("Gives you access to {0}.").format(", ".join(sections)) if sections else _("Gives you access to parts of Pathways.")
		)
		guide.append(
			{"role": role, "title": role.removeprefix("Pathways "), "summary": summary, "sections": sections, "approvals": approvals}
		)
	return guide


def _duration(seconds):
	"""'48 hours', '30 minutes'; '' for no expiry."""
	if not seconds:
		return ""
	value, unit = (seconds // 3600, "hour") if seconds >= 3600 else (max(seconds // 60, 1), "minute")
	return f"{value} {unit}{'' if value == 1 else 's'}"


def welcome_context(user, roles, added_by=None):
	"""Placeholders of the Staff Welcome email. Makes a fresh set-password
	link, so call it only when the email is really going out."""
	expiry = cint(frappe.get_system_settings("reset_password_link_expiry_duration"))
	guide = role_guide(roles)
	return {
		"user_name": user.get_fullname() or user.email,
		"login_email": user.email,
		"added_by": added_by or frappe.utils.get_fullname(frappe.session.user),
		"set_password_link": user.reset_password(),
		"link_expiry": _duration(expiry),
		"login_link": frappe.utils.get_url("/login?redirect-to=/pathways"),
		"roles": guide,
		"sections": list(dict.fromkeys(s for r in guide for s in r["sections"])),
	}


def send_staff_welcome(user):
	from pathways.utils.communication import send_event

	send_event(
		WELCOME_EVENT,
		"User",
		user.name,
		welcome_context(user, frappe.get_roles(user.name)),
		recipients=[{"email": user.email, "name": user.get_fullname()}],
	)
