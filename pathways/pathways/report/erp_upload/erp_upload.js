// Copyright (c) 2026, NLSIU and contributors
// For license information, please see license.txt

// Export with the report menu (Export > CSV / Excel) to load into the ERP.
frappe.query_reports["ERP Upload"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("Joined From"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("Joined To"),
			fieldtype: "Date",
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Pathways Department",
		},
	],
};
