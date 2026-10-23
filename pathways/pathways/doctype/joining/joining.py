# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""A selected candidate's joining (workflow step 31).

Draft      created when the offer is accepted, with the date the candidate gave
Confirmed  PnC has finalised the date: IT & Facilities are told (folder 12)
Joined     the person reported: Application -> Joined, Employee created
No-show    the person did not report; can be confirmed again for a new date

Rescheduling is just changing the date; the previous date and a count are
kept so the new joiner's report shows it, and IT is told again.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime, today

# status -> statuses it may move to
TRANSITIONS = {
	"Draft": {"Confirmed"},
	"Confirmed": {"Draft", "Joined", "No-show"},
	"No-show": {"Confirmed", "Draft"},
	"Joined": set(),
}


class Joining(Document):
	def validate(self):
		self.validate_prerequisites()
		self.set_details()
		self.validate_status_change()
		self.track_reschedule()

	def validate_prerequisites(self):
		"""Joining requires the Offer to have been Accepted — per brief §23,
		an Employee/Joining must never be creatable merely because an
		Application was marked Selected.
		"""
		if not self.application:
			return
		offer = frappe.db.get_value(
			"Offer Appointment Order", {"application": self.application}, ["name", "status"], as_dict=True
		)
		offer_status = offer.status if offer else None
		if offer_status != "Accepted":
			frappe.throw(
				"Joining cannot be recorded until the candidate's Offer has been Accepted "
				f"(current offer status: {offer_status or 'No Offer'})."
			)
		if not self.offer:
			self.offer = offer.name

	def set_details(self):
		app = frappe.db.get_value("Application", self.application, ["candidate", "job_opening"], as_dict=True)
		if not app:
			return
		self.candidate_name = frappe.db.get_value("Candidate", app.candidate, "full_name")
		self.job_opening = app.job_opening
		job = frappe.db.get_value("Job Opening", app.job_opening, ["designation", "department"], as_dict=True) or {}
		# The offer's designation/department win where the offer has them.
		offer = {}
		if self.offer:
			meta = frappe.get_meta("Offer Appointment Order")
			fields = [f for f in ("designation", "department") if meta.has_field(f)]
			if fields:
				offer = frappe.db.get_value("Offer Appointment Order", self.offer, fields, as_dict=True) or {}
		self.designation = offer.get("designation") or job.get("designation")
		self.department = offer.get("department") or job.get("department")

	def validate_status_change(self):
		self.status = self.status or "Draft"
		before = self.get_doc_before_save()
		previous = before.status if before else None
		if previous and previous != self.status and self.status not in TRANSITIONS.get(previous, set()):
			frappe.throw(_("A joining cannot move from {0} to {1}.").format(previous, self.status))

		if self.status in ("Confirmed", "Joined", "No-show") and not self.confirmed_doj:
			frappe.throw(_("Set the date of joining first."))

		if self.status == "Confirmed" and previous != "Confirmed":
			self.confirmed_by = frappe.session.user
			self.confirmed_on = now_datetime()

		if self.status == "Joined" and previous != "Joined":
			if getdate(self.confirmed_doj) > getdate(today()):
				frappe.throw(_("The joiner cannot be marked Joined before the date of joining ({0}).").format(
					frappe.utils.format_date(self.confirmed_doj)
				))
			self.actual_joining_date = self.actual_joining_date or self.confirmed_doj

	def track_reschedule(self):
		before = self.get_doc_before_save()
		if not before or not before.confirmed_doj or not self.confirmed_doj:
			return
		if getdate(before.confirmed_doj) == getdate(self.confirmed_doj):
			return
		if self.status == "Joined":
			frappe.throw(_("The date of joining cannot be changed after the joiner has joined."))
		self.previous_doj = before.confirmed_doj
		self.reschedule_count = cint(self.reschedule_count) + 1

	def on_update(self):
		from pathways.utils import onboarding

		status_changed = self.has_value_changed("status")
		if self.status == "Confirmed":
			details_changed = any(
				self.has_value_changed(f) for f in ("confirmed_doj", "reporting_location", "reporting_time")
			)
			if status_changed or details_changed:
				request = onboarding.ensure_it_request(self)
				# A re-confirmation after a no-show or a reschedule is an update.
				before = self.get_doc_before_save()
				updated = bool(not status_changed or (before and before.status == "No-show"))
				onboarding.notify_it_facilities(self, request, updated=updated)
		if self.status == "Joined" and status_changed:
			onboarding.on_joined(self)
