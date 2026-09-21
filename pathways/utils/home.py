# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Resolves the post-login home page for Pathways users.

Used as the get_website_user_home_page hook instead of a plain
role_home_page dict because frappe.get_roles("Administrator") returns
every role in the system — a dict lookup keyed by role name could
non-deterministically match "Pathways Candidate" first and misroute
the superuser account into the candidate portal.
"""

import frappe

from pathways.permissions import PATHWAYS_ROLES


def get_home_page(user):
	if user == "Administrator":
		return None

	roles = set(frappe.get_roles(user))
	if not roles & PATHWAYS_ROLES:
		return None

	if "Pathways Candidate" in roles and len(roles & PATHWAYS_ROLES) == 1:
		return "pathways/portal/jobs"

	return "pathways"
