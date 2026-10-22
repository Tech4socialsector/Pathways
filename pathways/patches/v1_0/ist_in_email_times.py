import frappe


def execute():
	"""Times in email variables now end in "IST" themselves, so drop the
	"(IST)" that saved templates wrote after them (edited ones too)."""
	for name, response, response_html in frappe.get_all(
		"Email Template", fields=["name", "response", "response_html"], as_list=True
	):
		values = {}
		for field, text in (("response", response), ("response_html", response_html)):
			if text and "(IST)" in text:
				new = text.replace("}} (IST)", "}}").replace("}}</b> (IST)", "}}</b>")
				if new != text:
					values[field] = new
		if values:
			frappe.db.set_value("Email Template", name, values, update_modified=False)
