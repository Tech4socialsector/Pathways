# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime


def send_templated_email(email_template, recipient, reference_doctype, reference_name, args=None):
	"""Send an email via a Frappe Email Template (Jinja-rendered) and log it
	to Communication Log, per the notification matrix in the architecture
	blueprint. Never call frappe.sendmail directly from business logic —
	always route through here so every recruitment email is auditable.
	"""
	status = "Sent"
	try:
		template = frappe.get_doc("Email Template", email_template)
		context = args or {}
		subject = frappe.render_template(template.subject, context)
		message = frappe.render_template(template.response, context)
		frappe.sendmail(recipients=[recipient], subject=subject, message=message)
	except Exception:
		status = "Failed"
		frappe.log_error(
			title=f"Pathways email send failed: {email_template} to {recipient}",
			reference_doctype=reference_doctype,
			reference_name=reference_name,
		)

	log = frappe.new_doc("Communication Log")
	log.reference_doctype = reference_doctype
	log.reference_name = reference_name
	log.email_template = email_template
	log.recipient = recipient
	log.sent_on = now_datetime()
	log.status = status
	log.insert(ignore_permissions=True)
	frappe.db.commit()
	return status
