# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data


def get_columns():
	return [
		{"label": "Job Opening", "fieldname": "job_opening", "fieldtype": "Link", "options": "Job Opening", "width": 220},
		{"label": "Track", "fieldname": "track", "fieldtype": "Link", "options": "Recruitment Track", "width": 100},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Applied", "fieldname": "applied", "fieldtype": "Int", "width": 90},
		{"label": "Eligible", "fieldname": "eligible", "fieldtype": "Int", "width": 90},
		{"label": "Shortlisted", "fieldname": "shortlisted", "fieldtype": "Int", "width": 100},
		{"label": "Interviewed", "fieldname": "interviewed", "fieldtype": "Int", "width": 100},
		{"label": "Selected", "fieldname": "selected", "fieldtype": "Int", "width": 90},
		{"label": "Offered", "fieldname": "offered", "fieldtype": "Int", "width": 90},
		{"label": "Joined", "fieldname": "joined", "fieldtype": "Int", "width": 90},
	]


def get_data(filters):
	conditions = {}
	if filters.get("track"):
		conditions["track"] = filters["track"]
	if filters.get("job_opening"):
		conditions["name"] = filters["job_opening"]

	job_openings = frappe.get_all(
		"Job Opening", filters=conditions, fields=["name", "track", "status"], order_by="creation desc"
	)

	rows = []
	for job in job_openings:
		applications = frappe.get_all("Application", filters={"job_opening": job.name}, pluck="name")
		applied = len(applications)
		if not applied:
			rows.append(
				{
					"job_opening": job.name,
					"track": job.track,
					"status": job.status,
					"applied": 0,
					"eligible": 0,
					"shortlisted": 0,
					"interviewed": 0,
					"selected": 0,
					"offered": 0,
					"joined": 0,
				}
			)
			continue

		eligible = frappe.db.count(
			"Eligibility Check", {"application": ["in", applications], "is_eligible": 1}
		)
		shortlisted = frappe.db.count(
			"Shortlisting Score", {"application": ["in", applications], "is_shortlisted": 1}
		)
		interviewed = frappe.db.count(
			"Interview", {"application": ["in", applications], "status": "Completed"}
		)
		selected = frappe.db.count(
			"Application", {"name": ["in", applications], "status": "Selected"}
		)
		offered = frappe.db.count(
			"Application",
			{"name": ["in", applications], "status": ["in", ["Offer Extended", "Offer Accepted", "Offer Declined"]]},
		)
		joined = frappe.db.count("Application", {"name": ["in", applications], "status": "Joined"})

		rows.append(
			{
				"job_opening": job.name,
				"track": job.track,
				"status": job.status,
				"applied": applied,
				"eligible": eligible,
				"shortlisted": shortlisted,
				"interviewed": interviewed,
				"selected": selected,
				"offered": offered,
				"joined": joined,
			}
		)

	return rows
