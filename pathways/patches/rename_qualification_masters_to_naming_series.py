# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Institution Master and Specialization Master moved from hash names to a
naming series. Rename existing records into the series (oldest first);
rename_doc also repoints the Link fields that reference them."""

import frappe
from frappe.model.naming import make_autoname
from frappe.model.rename_doc import rename_doc

SERIES = {
	"Institution Master": "PWY-INST-.####",
	"Specialization Master": "PWY-SPEC-.####",
}


def execute():
	for doctype, series in SERIES.items():
		prefix = series.split(".")[0]
		for name in frappe.get_all(doctype, order_by="creation asc", pluck="name"):
			if name.startswith(prefix):
				continue
			new_name = make_autoname(series, doctype)
			rename_doc(doctype, name, new_name, force=True, show_alert=False)
			frappe.db.set_value(doctype, new_name, "naming_series", series, update_modified=False)
