# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today


class OfferAppointmentOrder(Document):
	def validate(self):
		self.set_default_acceptance_deadline()
		self.sync_application_status()

	def set_default_acceptance_deadline(self):
		if self.status == "Sent" and not self.acceptance_deadline:
			settings = frappe.get_cached_doc("Pathways Settings")
			days = settings.acceptance_deadline_days or 7
			self.acceptance_deadline = add_days(self.offer_date or today(), days)

	def sync_application_status(self):
		if not self.application:
			return
		status_map = {
			"Sent": "Offer Extended",
			"Accepted": "Offer Accepted",
			"Declined": "Offer Declined",
		}
		new_status = status_map.get(self.status)
		if new_status:
			frappe.db.set_value("Application", self.application, "status", new_status)


@frappe.whitelist()
def respond_to_offer(offer_name, response, confirmed_doj=None, signed_copy_attachment=None):
	"""Candidate-facing accept/decline action, backing the Offer Response web form.
	Validates the candidate is responding to their own Offer and that it's still open.
	"""
	if response not in ("Accepted", "Declined"):
		frappe.throw("Invalid response.")

	offer = frappe.get_doc("Offer Appointment Order", offer_name)

	if offer.status != "Sent":
		frappe.throw(f"This offer is not currently open for a response (status: {offer.status}).")

	if getdate(offer.acceptance_deadline) < getdate(today()):
		frappe.throw("The acceptance deadline for this offer has passed.")

	application = frappe.get_doc("Application", offer.application)
	candidate_email = frappe.db.get_value("Candidate", application.candidate, "email")
	if frappe.session.user != "Administrator" and candidate_email != frappe.session.user:
		frappe.throw("You are not authorised to respond to this offer.")

	offer.status = response
	if response == "Accepted":
		if not confirmed_doj:
			frappe.throw("Please confirm your date of joining.")
		offer.candidate_confirmed_doj = confirmed_doj
		if signed_copy_attachment:
			offer.signed_copy_attachment = signed_copy_attachment

	offer.save(ignore_permissions=True)
	frappe.db.commit()
	return offer.status
