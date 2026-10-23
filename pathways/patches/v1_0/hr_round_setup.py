import frappe

from pathways.master_data import SCORING_RUBRICS

DEFAULT_CALENDAR_BLOCK_ROLES = ("Pathways Vice Chancellor", "Pathways Registrar")


def execute():
	"""Workflow steps 13-18: the Round 1 (HR interaction) assessment sheet
	per track, and the Pathways Settings defaults for HR assessors, the
	Selection Committee calendar block and assessment signatures. Only adds
	what is missing, so staff edits are kept."""
	seed_hr_rubrics()
	seed_interview_round_settings()


def seed_hr_rubrics():
	for spec in SCORING_RUBRICS:
		if spec["stage"] != "HR Interaction" or not frappe.db.exists("Recruitment Track", spec["track"]):
			continue
		if frappe.db.exists("Scoring Rubric Template", spec["rubric_name"]):
			continue
		if frappe.db.exists("Scoring Rubric Template", {"track": spec["track"], "stage": "HR Interaction", "is_active": 1}):
			continue
		frappe.get_doc(
			{
				"doctype": "Scoring Rubric Template",
				"rubric_name": spec["rubric_name"],
				"track": spec["track"],
				"stage": "HR Interaction",
				"scoring_mode": spec["scoring_mode"],
				"pass_threshold_percent": 50,
				"is_active": 1,
				"criteria": [{"criterion_label": label, "max_score": best, "guidance_text": guide} for label, best, guide in spec["criteria"]],
			}
		).insert(ignore_permissions=True)


def seed_interview_round_settings():
	settings = frappe.get_single("Pathways Settings")
	changed = False
	if not settings.get("hr_assessors_per_interview"):
		settings.hr_assessors_per_interview = 2
		changed = True
	if not settings.get("committee_block_hours"):
		settings.committee_block_hours = 3
		changed = True
	if not settings.get("calendar_block_roles"):
		for role in DEFAULT_CALENDAR_BLOCK_ROLES:
			if frappe.db.exists("Role", role):
				settings.append("calendar_block_roles", {"role": role})
				changed = True
	if changed:
		settings.flags.ignore_permissions = True
		settings.flags.ignore_mandatory = True
		settings.save()
