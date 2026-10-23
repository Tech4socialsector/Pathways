// Copyright (c) 2026, NLSIU and contributors
// For license information, please see license.txt

frappe.query_reports["New Joiners"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("Joining From"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
		},
		{
			fieldname: "to_date",
			label: __("Joining To"),
			fieldtype: "Date",
			default: frappe.datetime.month_end(),
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Draft", "Confirmed", "Joined", "No-show"],
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Pathways Department",
		},
	],
};
