# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, getdate, now_datetime, today


def daily():
	flag_ads_closing_soon()
	expire_overdue_offers()
	send_interview_reminders()


def flag_ads_closing_soon():
	"""Confirmed source SLA: ad extension decision checked ~1 day before
	the ad's end date. Flags via ToDo rather than auto-extending, since
	extension is a human judgment call.
	"""
	tomorrow = add_days(today(), 1)
	closing_soon = frappe.get_all(
		"Recruitment Notification",
		filters={"status": "Published", "closing_datetime": ["between", [today(), tomorrow]]},
		fields=["name", "job_opening"],
	)
	for notif in closing_soon:
		if frappe.db.exists(
			"ToDo", {"reference_type": "Recruitment Notification", "reference_name": notif.name, "status": "Open"}
		):
			continue
		todo = frappe.new_doc("ToDo")
		todo.description = (
			f"Advertisement for {notif.job_opening} closes within 24 hours. "
			f"Decide whether to extend (issue a Corrigendum) or let it close."
		)
		todo.reference_type = "Recruitment Notification"
		todo.reference_name = notif.name
		todo.insert(ignore_permissions=True)
	frappe.db.commit()


def expire_overdue_offers():
	overdue = frappe.get_all(
		"Offer Appointment Order",
		filters={"status": "Sent", "acceptance_deadline": ["<", today()]},
		pluck="name",
	)
	for offer_name in overdue:
		frappe.db.set_value("Offer Appointment Order", offer_name, "status", "Expired")
		application = frappe.db.get_value("Offer Appointment Order", offer_name, "application")
		if application:
			frappe.db.set_value("Application", application, "status", "Not Selected")
	if overdue:
		frappe.db.commit()


def send_interview_reminders():
	"""T-1 day reminder for scheduled interviews."""
	from pathways.utils.communication import send_templated_email

	tomorrow = add_days(today(), 1)
	upcoming = frappe.get_all(
		"Interview",
		filters={"status": "Scheduled", "scheduled_datetime": ["between", [today(), tomorrow]]},
		fields=["name", "application"],
	)
	if not upcoming:
		return

	if not frappe.db.exists("Email Template", "Interview Reminder"):
		return

	for interview in upcoming:
		candidate = frappe.db.get_value(
			"Candidate", frappe.db.get_value("Application", interview.application, "candidate"), "email"
		)
		if candidate:
			send_templated_email(
				"Interview Reminder", candidate, "Interview", interview.name, {"interview": interview.name}
			)
