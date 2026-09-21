# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Employee(Document):
	def validate(self):
		if self.is_new():
			self.validate_creation_gate()

	def validate_creation_gate(self):
		"""An Employee must never be auto-created merely because an
		Application is 'Selected' — requires a Joining record AND all
		mandatory Document Collection items Verified, per brief §23.
		"""
		if not self.source_application:
			frappe.throw("Employee must be linked to a Source Application.")

		joining = frappe.db.exists("Joining", {"application": self.source_application})
		if not joining:
			frappe.throw("Cannot create Employee: no Joining record exists for this Application.")

		doc_collection = frappe.db.get_value(
			"Document Collection", {"application": self.source_application}, "overall_status"
		)
		if doc_collection != "Complete":
			frappe.throw(
				f"Cannot create Employee: Document Collection is not Complete "
				f"(current status: {doc_collection or 'No Document Collection'})."
			)


@frappe.whitelist()
def create_employee_from_application(application_name):
	"""Explicit, gate-checked Employee creation entry point."""
	application = frappe.get_doc("Application", application_name)
	candidate = frappe.get_doc("Candidate", application.candidate)
	job_opening = frappe.get_doc("Job Opening", application.job_opening)
	joining = frappe.get_doc("Joining", {"application": application_name})

	employee = frappe.new_doc("Employee")
	employee.employee_name = candidate.full_name
	employee.designation = job_opening.designation
	employee.department = job_opening.department
	employee.date_of_joining = joining.confirmed_doj
	employee.employment_type = job_opening.employment_type
	employee.source_application = application_name
	employee.insert(ignore_permissions=True)

	if not frappe.db.exists("User", candidate.email):
		user = frappe.new_doc("User")
		user.email = candidate.email
		user.first_name = candidate.full_name
		user.send_welcome_email = 1
		user.insert(ignore_permissions=True)
		employee.user = candidate.email
		employee.save(ignore_permissions=True)

	application.status = "Joined"
	application.save(ignore_permissions=True)

	frappe.db.commit()
	return employee.name
