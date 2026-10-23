# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe


def commit():
	"""Commit, except under tests. Background jobs and scheduled tasks commit
	so their work survives; in a test run the same commit would also keep the
	test's own records, which then pile up on the development site."""
	if getattr(frappe, "in_test", False) or frappe.flags.in_test:
		return
	frappe.db.commit()
