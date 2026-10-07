# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Pathways Candidate must not have desk access: Frappe turns a Website User
given such a role into a System User, which let a candidate into Desk and
blocked their next application ("Staff accounts cannot apply"). Users who
were converted only by this role are turned back into Website Users."""

import frappe

from pathways.permissions import CANDIDATE_ROLE


def execute():
	if not frappe.db.exists("Role", CANDIDATE_ROLE):
		return
	frappe.db.set_value("Role", CANDIDATE_ROLE, "desk_access", 0)

	desk_roles = set(frappe.get_all("Role", filters={"desk_access": 1}, pluck="name"))
	for user in frappe.get_all("Has Role", filters={"role": CANDIDATE_ROLE, "parenttype": "User"}, pluck="parent"):
		if user in ("Administrator", "Guest") or frappe.db.get_value("User", user, "user_type") != "System User":
			continue
		roles = set(frappe.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role"))
		if not roles & desk_roles:
			frappe.db.set_value("User", user, "user_type", "Website User")
