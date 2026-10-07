# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Bulk actions from list pages: run a per-record action on each selected
record with all its usual checks, so one failure (no permission, a
validation rule) skips that record instead of stopping the rest."""

import frappe
from frappe import _

BULK_LIMIT = 500


def run_bulk(names, action):
	"""action(name) for each name, each in its own savepoint. Returns
	{"done": [names], "failed": [{"name", "error"}]}."""
	if isinstance(names, str):
		names = frappe.parse_json(names)
	names = list(dict.fromkeys(names or []))
	if len(names) > BULK_LIMIT:
		frappe.throw(_("Select at most {0} records at a time.").format(BULK_LIMIT))

	done, failed = [], []
	for name in names:
		savepoint = f"bulk_{len(done) + len(failed)}"
		frappe.db.savepoint(savepoint)
		try:
			action(name)
			done.append(name)
		except Exception as e:
			frappe.db.rollback(save_point=savepoint)
			messages = [m.get("message") if isinstance(m, dict) else str(m) for m in frappe.local.message_log or []]
			failed.append({"name": name, "error": frappe.utils.strip_html(messages[-1] if messages else str(e)) or _("Failed")})
		finally:
			frappe.local.message_log = []
	return {"done": done, "failed": failed}
