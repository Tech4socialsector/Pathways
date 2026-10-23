# Copyright (c) 2026, NLSIU and contributors
# For license information, please see license.txt

"""The NLSIU letterhead on every Pathways print and PDF.

One Frappe Letter Head ("NLSIU", editable in Desk > Letter Head) is the
single source: Desk print views show it as the default letter head, and the
PDFs built in code (offer letter, assessment forms, schedules, panel
details, HR notes, shortlisting note) put the same rendered content at the
top. It follows NLSIU's official notifications: the crest on the left, the
university's name and address in bold beside it.

The crest is the logo set in Pathways Settings (Appearance) and is embedded
as a data URI, because the PDF renderer cannot always fetch a /files/ URL
back from the site it is running on."""

import base64
import mimetypes

import frappe

LETTER_HEAD = "NLSIU"

# Jinja, rendered by Frappe for print views and by letterhead_html() for PDFs.
CONTENT = """{% set logo = pathways_logo_src() %}
<table style="width:100%; border-collapse:collapse; margin:0 0 14px; font-family:'Times New Roman', Times, serif;">
<tr>
{% if logo %}<td style="width:78px; padding:0 12px 0 0; vertical-align:middle; border:none;"><img src="{{ logo }}" alt="NLSIU" style="height:72px; width:auto;"></td>{% endif %}
<td style="vertical-align:middle; border:none; padding:0; font-weight:bold; font-size:12pt; line-height:1.35; color:#111; text-align:left;">
NATIONAL LAW SCHOOL OF INDIA UNIVERSITY<br>NAGARBHAVI, BANGALORE - 560242
</td>
</tr>
</table>"""

FALLBACK_TEXT = "NATIONAL LAW SCHOOL OF INDIA UNIVERSITY<br>NAGARBHAVI, BANGALORE - 560242"


def pathways_logo_src():
	"""The Pathways Settings logo as a data URI, or "" when none is set or the
	file is missing. Registered as a Jinja method (hooks.jinja)."""
	url = frappe.db.get_single_value("Pathways Settings", "app_logo")
	if not url:
		return ""
	if url.startswith(("data:", "http://", "https://")):
		return url
	try:
		file = frappe.get_doc("File", {"file_url": url})
		content = file.get_content()
	except Exception:
		return ""
	if isinstance(content, str):
		content = content.encode()
	mime = mimetypes.guess_type(url)[0] or "image/png"
	return f"data:{mime};base64,{base64.b64encode(content).decode()}"


def letterhead_html(doc=None):
	"""Rendered letterhead for PDFs built in code: the NLSIU Letter Head, or
	the same layout from code if it has been deleted."""
	content = frappe.db.get_value("Letter Head", LETTER_HEAD, "content") or CONTENT
	try:
		return frappe.render_template(content, {"doc": doc or {}})
	except Exception:
		frappe.log_error(title="Pathways letterhead could not be rendered")
		return f'<div style="font-weight:bold; margin-bottom:14px;">{FALLBACK_TEXT}</div>'


def pathways_letterhead(doc=None):
	"""Jinja method for the Pathways print formats. They are custom formats,
	which Frappe does not wrap in a letter head, so each one places it."""
	return letterhead_html(doc)


def ensure_letter_head():
	"""Create the NLSIU Letter Head once (staff edits are kept) and make it
	the default when the site has none."""
	if not frappe.db.exists("Letter Head", LETTER_HEAD):
		frappe.get_doc(
			{
				"doctype": "Letter Head",
				"letter_head_name": LETTER_HEAD,
				"source": "HTML",
				"content": CONTENT,
				"is_default": 0,
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Letter Head", {"is_default": 1, "disabled": 0}):
		frappe.db.set_value("Letter Head", LETTER_HEAD, "is_default", 1)
