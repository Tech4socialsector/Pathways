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

from pathways.permissions import CANDIDATE_ROLE, get_pathways_roles


def get_home_page(user):
	if user == "Administrator":
		return None

	pathways_roles = get_pathways_roles()
	roles = set(frappe.get_roles(user))
	if not roles & pathways_roles:
		return None

	if CANDIDATE_ROLE in roles and len(roles & pathways_roles) == 1:
		return "pathways/portal/jobs"

	return "pathways"
