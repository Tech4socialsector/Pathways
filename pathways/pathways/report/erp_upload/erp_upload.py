# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""ERP Upload: people who have joined, one flat row each, in the column
order the ERP's employee import expects, so PnC can export it (CSV/Excel
from the report menu) instead of retyping. Pay comes from the offer when
the offer carries it; offer fields are read only if the Offer DocType has
them, so this keeps working while the offer form evolves."""

import frappe
from frappe import _

# (offer fieldname, column label, fieldtype)
OFFER_PAY_FIELDS = (
	("pay_level", "Pay Level", "Data"),
	("pay_scale", "Pay Scale", "Data"),
	("gross_monthly_salary", "Gross Monthly Salary", "Currency"),
	("consolidated_fee", "Consolidated Fee", "Currency"),
	("allowances", "Allowances", "Data"),
)


def execute(filters=None):
	filters = frappe._dict(filters or {})
	pay_fields = _offer_pay_fields()
	return get_columns(pay_fields), get_data(filters, pay_fields)


def _offer_pay_fields():
	meta = frappe.get_meta("Offer Appointment Order")
	return [f for f in OFFER_PAY_FIELDS if meta.has_field(f[0])]


def get_columns(pay_fields):
	columns = [
		{"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Pathways Employee", "width": 140},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": _("Gender"), "fieldname": "gender", "fieldtype": "Data", "width": 80},
		{"label": _("Date of Birth"), "fieldname": "date_of_birth", "fieldtype": "Date", "width": 100},
		{"label": _("Designation"), "fieldname": "designation", "fieldtype": "Data", "width": 170},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 170},
		{"label": _("Date of Joining"), "fieldname": "date_of_joining", "fieldtype": "Date", "width": 110},
		{"label": _("Employment Type"), "fieldname": "employment_type", "fieldtype": "Data", "width": 120},
		{"label": _("Official Email"), "fieldname": "official_email", "fieldtype": "Data", "width": 200},
		{"label": _("Personal Email"), "fieldname": "personal_email", "fieldtype": "Data", "width": 200},
		{"label": _("Mobile"), "fieldname": "mobile", "fieldtype": "Data", "width": 120},
		{"label": _("Reporting Manager"), "fieldname": "reporting_manager", "fieldtype": "Data", "width": 150},
		{"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 80},
		{"label": _("Address"), "fieldname": "address", "fieldtype": "Data", "width": 220},
	]
	for fieldname, label, fieldtype in pay_fields:
		columns.append({"label": _(label), "fieldname": fieldname, "fieldtype": fieldtype, "width": 130})
	columns.append({"label": _("Application ID"), "fieldname": "application_id", "fieldtype": "Data", "width": 140})
	return columns


def get_data(filters, pay_fields):
	conditions = {"status": "Joined"}
	if filters.from_date and filters.to_date:
		conditions["actual_joining_date"] = ["between", [filters.from_date, filters.to_date]]
	elif filters.from_date:
		conditions["actual_joining_date"] = [">=", filters.from_date]
	elif filters.to_date:
		conditions["actual_joining_date"] = ["<=", filters.to_date]
	if filters.department:
		conditions["department"] = filters.department

	joinings = frappe.get_list(
		"Joining",
		filters=conditions,
		fields=[
			"name", "application", "offer", "candidate_name", "designation", "department", "confirmed_doj",
			"actual_joining_date", "reporting_manager", "employee", "it_facilities_request",
		],
		order_by="actual_joining_date asc",
		limit_page_length=0,
	)
	rows = []
	for j in joinings:
		app = frappe.db.get_value("Application", j.application, ["application_id", "candidate", "job_opening"], as_dict=True) or {}
		person = frappe.db.get_value(
			"Candidate", app.get("candidate"), ["full_name", "email", "mobile_number", "gender", "date_of_birth", "category", "address"], as_dict=True
		) or {}
		job = frappe.db.get_value("Job Opening", app.get("job_opening"), ["employment_type", "pay_level"], as_dict=True) or {}
		employee = frappe.db.get_value("Pathways Employee", j.employee, ["employee_name", "employment_type"], as_dict=True) if j.employee else None
		offer = {}
		if j.offer and pay_fields:
			offer = frappe.db.get_value("Offer Appointment Order", j.offer, [f[0] for f in pay_fields], as_dict=True) or {}
		row = {
			"employee": j.employee,
			"employee_name": (employee or {}).get("employee_name") or person.get("full_name") or j.candidate_name,
			"gender": person.get("gender"),
			"date_of_birth": person.get("date_of_birth"),
			"designation": j.designation,
			"department": j.department,
			"date_of_joining": j.actual_joining_date or j.confirmed_doj,
			"employment_type": (employee or {}).get("employment_type") or job.get("employment_type"),
			"official_email": frappe.db.get_value("IT Facilities Provisioning Request", j.it_facilities_request, "official_email")
			if j.it_facilities_request
			else None,
			"personal_email": person.get("email"),
			"mobile": person.get("mobile_number"),
			"reporting_manager": j.reporting_manager,
			"category": person.get("category"),
			"address": (person.get("address") or "").replace("\n", ", "),
			"application_id": app.get("application_id"),
		}
		for fieldname, _label, _type in pay_fields:
			row[fieldname] = offer.get(fieldname)
		if "pay_level" in row and not row["pay_level"]:
			row["pay_level"] = job.get("pay_level")
		rows.append(row)
	return rows
