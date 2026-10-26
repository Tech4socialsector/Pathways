# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""New Joiners: the register PnC keeps of who joins when (workflow step 31,
"updating the same in new joiner's report"). One row per Joining whose
date of joining falls in the period, with where the onboarding stands
(documents, IT & Facilities)."""

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{"label": _("Joining"), "fieldname": "name", "fieldtype": "Link", "options": "Joining", "width": 150},
		{"label": _("Name"), "fieldname": "candidate_name", "fieldtype": "Data", "width": 180},
		{"label": _("Application ID"), "fieldname": "application_id", "fieldtype": "Data", "width": 140},
		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Link", "options": "Pathways Designation", "width": 170},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Pathways Department", "width": 170},
		{"label": _("Track"), "fieldname": "track", "fieldtype": "Data", "width": 90},
		{"label": _("Employment Type"), "fieldname": "employment_type", "fieldtype": "Data", "width": 120},
		{"label": _("Date of Joining"), "fieldname": "confirmed_doj", "fieldtype": "Date", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Times Rescheduled"), "fieldname": "reschedule_count", "fieldtype": "Int", "width": 90},
		{"label": _("Reporting Location"), "fieldname": "reporting_location", "fieldtype": "Data", "width": 200},
		{"label": _("Reporting Time"), "fieldname": "reporting_time", "fieldtype": "Time", "width": 90},
		{"label": _("Reporting Manager"), "fieldname": "reporting_manager", "fieldtype": "Data", "width": 150},
		{"label": _("Email"), "fieldname": "email", "fieldtype": "Data", "width": 200},
		{"label": _("Mobile"), "fieldname": "mobile", "fieldtype": "Data", "width": 120},
		{"label": _("Documents"), "fieldname": "document_status", "fieldtype": "Data", "width": 140},
		{"label": _("IT & Facilities"), "fieldname": "it_status", "fieldtype": "Data", "width": 110},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 140},
	]


def get_data(filters):
	conditions = {}
	if filters.from_date and filters.to_date:
		conditions["confirmed_doj"] = ["between", [filters.from_date, filters.to_date]]
	elif filters.from_date:
		conditions["confirmed_doj"] = [">=", filters.from_date]
	elif filters.to_date:
		conditions["confirmed_doj"] = ["<=", filters.to_date]
	if filters.status:
		conditions["status"] = filters.status
	if filters.department:
		conditions["department"] = filters.department

	rows = frappe.get_list(
		"Joining",
		filters=conditions,
		fields=[
			"name", "application", "candidate_name", "designation", "department", "confirmed_doj", "status", "reschedule_count",
			"reporting_location", "reporting_time", "reporting_manager", "it_facilities_request", "employee",
		],
		order_by="confirmed_doj asc",
		limit_page_length=0,
	)
	for row in rows:
		app = frappe.db.get_value("Application", row.application, ["application_id", "candidate", "job_opening"], as_dict=True) or {}
		person = frappe.db.get_value("Candidate", app.get("candidate"), ["email", "mobile_number"], as_dict=True) or {}
		job = frappe.db.get_value("Job Opening", app.get("job_opening"), ["track", "employment_type"], as_dict=True) or {}
		row.application_id = app.get("application_id")
		row.email = person.get("email")
		row.mobile = person.get("mobile_number")
		row.track = job.get("track")
		row.employment_type = job.get("employment_type")
		row.document_status = frappe.db.get_value("Document Collection", {"application": row.application}, "overall_status") or ""
		row.it_status = (
			frappe.db.get_value("IT Facilities Provisioning Request", row.it_facilities_request, "status")
			if row.it_facilities_request
			else ""
		)
	return rows
