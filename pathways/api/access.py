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
	get_pathways_roles,
	has_full_access,
)
from pathways.utils.approval import is_approver
from pathways.utils.master_setup import MASTER_SETUP, can_manage

MANAGER_ROLE = "System Manager"
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
	{"key": "applications", "label": "Applications", "doctype": "Application"},
	{"key": "interviews", "label": "Interviews", "doctype": "Interview"},
	{"key": "offers", "label": "Offers", "doctype": "Offer Appointment Order"},
	{"key": "documents", "label": "Documents", "doctype": "Document Collection"},
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
		for doctype in ("Pre-Recruitment Green Sheet", "Pathways Settings"):
			doctypes[doctype] = _doctype_perms(doctype)
		if is_approver(user):
			menu.append("approvals")
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
		"can_manage_access": MANAGER_ROLE in all_roles,
		"can_manage_settings": bool(doctypes.get("Pathways Settings", {}).get("write")),
	}


# ------------------------------------------------------ System Manager API


def _only_manager():
	frappe.only_for(MANAGER_ROLE)


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

	if not frappe.db.exists("Role", role_name):
		frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": cint(desk_access)}).insert()

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
	frappe.get_doc("User", user).add_roles(role)
	return True


@frappe.whitelist(methods=["POST"])
def unassign_role(user, role):
	_only_manager()
	if role not in get_pathways_roles():
		frappe.throw(_("{0} is not a Pathways role.").format(role))
	frappe.get_doc("User", user).remove_roles(role)
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

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": (first_name or "").strip() or email,
			"last_name": (last_name or "").strip() or None,
			"user_type": "System User",
			"send_welcome_email": 1,
		}
	)
	user.insert()
	if roles:
		user.add_roles(*roles)
	return user.name
