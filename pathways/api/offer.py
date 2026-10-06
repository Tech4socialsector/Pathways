# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe

from pathways.permissions import has_full_access
from pathways.pathways.doctype.offer_appointment_order.offer_appointment_order import (
	respond_to_offer as _respond_to_offer,
)


@frappe.whitelist()
def get_my_offer(application_name):
	app = frappe.get_doc("Application", application_name)
	app.check_permission("read")
	candidate_email = frappe.db.get_value("Candidate", app.candidate, "email")
	if frappe.session.user != candidate_email and not has_full_access("Offer Appointment Order"):
		frappe.throw("You are not authorised to view this offer.", frappe.PermissionError)

	offer_name = frappe.db.get_value("Offer Appointment Order", {"application": application_name}, "name")
	if not offer_name:
		return None

	offer = frappe.get_doc("Offer Appointment Order", offer_name)
	return {
		"name": offer.name,
		"status": offer.status,
		"offer_date": offer.offer_date,
		"acceptance_deadline": offer.acceptance_deadline,
		"candidate_confirmed_doj": offer.candidate_confirmed_doj,
	}


@frappe.whitelist()
def respond_to_offer(offer_name, response, confirmed_doj=None, signed_copy_attachment=None):
	return _respond_to_offer(offer_name, response, confirmed_doj, signed_copy_attachment)
