# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""Offer / appointment order for one selected candidate (workflow steps
22-29).

Lifecycle: Draft -> Under Review -> Approved for Signature -> Signed by
Registrar -> Sent -> Accepted / Declined / Expired, with "return for
changes" back to Draft from review or signing. The actions live in
pathways.api.offer; this controller only holds the rules that must hold
however the record is saved (green-sheet gate, history, application
status). Every status change goes through a normal save() so other apps'
doc_events (e.g. onboarding on Accepted) fire.

"Verbal Offer" and "Drafted" are statuses from before the review step;
they are treated as Draft."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, now_datetime, today

DRAFT_STATUSES = ("Draft", "Verbal Offer", "Drafted")
# What a candidate may see; earlier statuses are internal working drafts.
CANDIDATE_VISIBLE_STATUSES = ("Sent", "Accepted", "Declined", "Expired")
APPLICATION_STATUS = {
	"Sent": "Offer Extended",
	"Accepted": "Offer Accepted",
	"Declined": "Offer Declined",
	"Expired": "Not Selected",
}


def find_approved_green_sheet(application):
	"""The approved (submitted) Post-Interview Green Sheet that names this
	application as recommended or waitlisted. Queried directly so this does
	not depend on the green sheet module's API."""
	if not application or not frappe.db.exists("DocType", "Post-Interview Green Sheet"):
		return None
	meta = frappe.get_meta("Post-Interview Green Sheet")
	or_filters = {f: application for f in ("recommended_application", "waitlist_application") if meta.has_field(f)}
	if not or_filters:
		return None
	sheets = frappe.get_all(
		"Post-Interview Green Sheet",
		filters={"status": "Approved", "docstatus": 1},
		or_filters=or_filters,
		pluck="name",
		order_by="modified desc",
		limit=1,
	)
	return sheets[0] if sheets else None


def green_sheet_required():
	value = frappe.get_cached_doc("Pathways Settings").get("offer_requires_green_sheet")
	return value is None or bool(value)


class OfferAppointmentOrder(Document):
	def validate(self):
		if self.status in (None, ""):
			self.status = "Draft"
		self.check_green_sheet()
		self.set_default_acceptance_deadline()
		self.log_status_change()
		self.sync_application_status()

	def check_green_sheet(self):
		"""Step 24-25 must be done before step 26: the candidate has to be on
		an approved Post-Interview Green Sheet (unless Settings relaxes it)."""
		before = self.get_doc_before_save()
		if before and before.application == self.application and self.post_interview_green_sheet:
			return
		sheet = find_approved_green_sheet(self.application)
		if sheet:
			self.post_interview_green_sheet = sheet
		elif self.is_new() and green_sheet_required():
			frappe.throw(
				_(
					"An offer can only be created for a candidate recommended or waitlisted on an approved "
					"Post-Interview Green Sheet. Get the green sheet approved first."
				),
				title=_("Green Sheet Not Approved"),
			)

	def set_default_acceptance_deadline(self):
		if self.status == "Sent" and not self.acceptance_deadline:
			settings = frappe.get_cached_doc("Pathways Settings")
			days = settings.acceptance_deadline_days or 7
			self.acceptance_deadline = add_days(self.offer_date or today(), days)

	def log_status_change(self):
		before = self.get_doc_before_save()
		previous = before.status if before else None
		if previous == self.status:
			return
		self.append(
			"status_log",
			{
				"from_status": previous,
				"to_status": self.status,
				"action": self.flags.get("offer_action") or (_("Created") if not previous else _("Status changed")),
				"user": frappe.session.user,
				"timestamp": now_datetime(),
				"remarks": self.flags.get("offer_remarks"),
			},
		)

	def sync_application_status(self):
		if not self.application:
			return
		before = self.get_doc_before_save()
		if before and before.status == self.status:
			return
		new_status = APPLICATION_STATUS.get(self.status)
		if new_status:
			frappe.db.set_value("Application", self.application, "status", new_status)


@frappe.whitelist()
def respond_to_offer(offer_name, response, confirmed_doj=None, signed_copy_attachment=None, decline_reason=None):
	"""Candidate-facing accept/decline action (portal). Validates the
	candidate is responding to their own Offer and that it's still open."""
	if response not in ("Accepted", "Declined"):
		frappe.throw(_("Invalid response."))

	offer = frappe.get_doc("Offer Appointment Order", offer_name)

	application = frappe.get_doc("Application", offer.application)
	candidate_email = frappe.db.get_value("Candidate", application.candidate, "email")
	if frappe.session.user != "Administrator" and candidate_email != frappe.session.user:
		frappe.throw(_("You are not authorised to respond to this offer."), frappe.PermissionError)

	if offer.status != "Sent":
		frappe.throw(_("This offer is not currently open for a response (status: {0}).").format(offer.status))

	if offer.acceptance_deadline and getdate(offer.acceptance_deadline) < getdate(today()):
		frappe.throw(_("The acceptance deadline for this offer has passed."))

	offer.status = response
	offer.responded_on = now_datetime()
	offer.flags.offer_action = _("Accepted by candidate") if response == "Accepted" else _("Declined by candidate")
	if response == "Accepted":
		if not confirmed_doj:
			frappe.throw(_("Please confirm your date of joining."))
		if getdate(confirmed_doj) < getdate(today()):
			frappe.throw(_("The date of joining cannot be in the past."))
		offer.candidate_confirmed_doj = confirmed_doj
		if signed_copy_attachment:
			from pathways.api.offer import claim_file

			offer.signed_copy_attachment = claim_file(signed_copy_attachment, offer, "signed_copy_attachment")
	else:
		offer.decline_reason = decline_reason
		offer.flags.offer_remarks = decline_reason

	# No explicit commit: the request commits on success, and tests roll back.
	offer.save(ignore_permissions=True)
	return offer.status


def expire_overdue_offers():
	"""Daily: Sent offers past their acceptance deadline become Expired.
	Saved one by one (not set_value) so history, the application status and
	other apps' hooks all see the change."""
	overdue = frappe.get_all(
		"Offer Appointment Order",
		filters=[
			["status", "=", "Sent"],
			["acceptance_deadline", "is", "set"],
			["acceptance_deadline", "<", today()],
		],
		pluck="name",
	)
	for offer_name in overdue:
		offer = frappe.get_doc("Offer Appointment Order", offer_name)
		offer.status = "Expired"
		offer.flags.offer_action = _("Expired: no response by the deadline")
		offer.flags.ignore_permissions = True
		offer.save()
	if overdue and not frappe.flags.in_test:
		frappe.db.commit()
	return overdue
