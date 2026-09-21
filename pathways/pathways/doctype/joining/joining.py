# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Joining(Document):
	def validate(self):
		self.validate_prerequisites()

	def validate_prerequisites(self):
		"""Joining requires the Offer to have been Accepted — per brief §23,
		an Employee/Joining must never be creatable merely because an
		Application was marked Selected.
		"""
		if not self.application:
			return
		offer_status = frappe.db.get_value(
			"Offer Appointment Order", {"application": self.application}, "status"
		)
		if offer_status != "Accepted":
			frappe.throw(
				"Joining cannot be recorded until the candidate's Offer has been Accepted "
				f"(current offer status: {offer_status or 'No Offer'})."
			)

	def after_insert(self):
		self.create_it_facilities_request()

	def create_it_facilities_request(self):
		if self.it_facilities_request:
			return

		application = frappe.get_doc("Application", self.application)
		candidate = frappe.get_doc("Candidate", application.candidate)
		job_opening = frappe.get_doc("Job Opening", application.job_opening)

		request = frappe.new_doc("IT Facilities Provisioning Request")
		request.joining = self.name
		request.employee_name = candidate.full_name
		request.designation = job_opening.designation or job_opening.job_title
		request.date_of_joining = self.confirmed_doj
		request.personal_email = candidate.email
		request.mobile_number = candidate.mobile_number
		request.insert(ignore_permissions=True)

		self.db_set("it_facilities_request", request.name)
		frappe.db.commit()
