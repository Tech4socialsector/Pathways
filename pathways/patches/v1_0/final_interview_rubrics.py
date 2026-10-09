import frappe

from pathways.master_data import SCORING_RUBRICS


def execute():
	"""Workflow folder "6. Final Interview / Interview Assessment Form": each
	track's active Final Interview rubric gets the form's criteria, best
	scores and questions, and the 50% bar for an offer."""
	for spec in SCORING_RUBRICS:
		if spec["stage"] != "Final Interview":
			continue
		names = frappe.get_all("Scoring Rubric Template", filters={"track": spec["track"], "stage": "Final Interview", "is_active": 1}, pluck="name")
		for name in names:
			doc = frappe.get_doc("Scoring Rubric Template", name)
			doc.scoring_mode = "Weighted Score"
			doc.pass_threshold_percent = 50
			doc.set("criteria", [{"criterion_label": label, "max_score": best, "guidance_text": guide} for label, best, guide in spec["criteria"]])
			doc.flags.ignore_permissions = True
			doc.save()
