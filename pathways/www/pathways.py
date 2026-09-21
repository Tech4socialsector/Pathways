# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint

no_cache = 1


def get_context():
	"""Serves the Pathways SPA shell. The SPA's own router (Vue Router)
	further gates staff-only routes client-side, but every staff API call
	is independently permission-checked server-side (has_permission /
	permission_query_conditions in pathways/permissions.py) — the route
	guard here is only about who gets the page at all, not what they can
	do once loaded. Candidate-portal routes (job board, apply, status)
	must remain reachable as a Guest.
	"""
	frappe.db.commit()
	context = frappe._dict()
	context.boot = get_boot()
	return context


def get_boot():
	return frappe._dict(
		{
			"frappe_version": frappe.__version__,
			"site_name": frappe.local.site,
			"csrf_token": frappe.sessions.get_csrf_token(),
			"setup_complete": cint(frappe.get_system_settings("setup_complete")),
		}
	)
