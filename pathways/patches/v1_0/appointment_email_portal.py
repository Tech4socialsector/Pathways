"""The appointment order covering email now points the candidate to the
portal to accept or decline (the old text only asked for an email reply).
Updated only where the template still has the old default text exactly,
so wording edited in Email Setup is kept."""

import frappe

from pathways.utils.email_events import TEMPLATES

NAME = "Appointment Order Covering Note"
OLD_DEFAULT = (
	"<p>Dear {{ candidate_name }},</p>"
	"<p>Greetings from the National Law School of India University, Bangalore!</p>"
	"<p>Please find attached the Appointment Letter as {{ job_title }} at NLSIU. Request you to confirm your acceptance "
	"and send a signed scanned copy of the appointment letter with a reply all to this email by "
	"<b>{{ acceptance_deadline }}</b>.</p>"
	"<p>Please also indicate your earliest date of joining in the same email.</p>"
	"<p>You may get in touch with {{ pnc_contacts or 'the People and Culture team' }}"
	"{% if pnc_contacts %}, from the People and Culture team,{% endif %} if you need any further clarifications or support.</p>"
	"<p>Regards,<br>Registrar's Office</p>"
)


def execute():
	if not frappe.db.exists("Email Template", NAME):
		return
	current = frappe.db.get_value("Email Template", NAME, ["response", "response_html", "use_html"], as_dict=True)
	unchanged = [f for f in ("response", "response_html") if (current.get(f) or "").strip() == OLD_DEFAULT]
	if not unchanged:
		return  # edited in Email Setup (or already updated): keep it
	_subject, response = TEMPLATES[NAME]
	frappe.db.set_value("Email Template", NAME, {f: response for f in unchanged})
