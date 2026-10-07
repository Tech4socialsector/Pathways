import frappe

# Workflow folder "4. Shortlisting": the criteria and best scores the
# committees use in their sheets.
RUBRICS = {
	"Faculty Shortlisting Rubric": [
		("Education (without PhD)", 50, "UG and PG: institution score + CAS score, as in the Eligibility Check & Scoring sheet. PhD is not counted here."),
		("Publications", 10, "Peer-reviewed / UGC-listed journal publications, books and book chapters."),
		("Teaching Experience", 5, "Points per year of teaching experience (all teaching posts), up to 5."),
		("Administrative Experience", 5, "Points per administrative / institutional post held, up to 5."),
	],
	"Research Shortlisting Rubric": [
		("Education", 4, "REF DOC - CV"),
		("Overall Experience + SOP", 4, "REF DOC - Experience + SOP + one writing sample + research publication"),
		("Overall", 4, "REF DOC - CV"),
	],
}


def execute():
	for name, criteria in RUBRICS.items():
		if not frappe.db.exists("Scoring Rubric Template", name):
			continue
		doc = frappe.get_doc("Scoring Rubric Template", name)
		doc.scoring_mode = "Weighted Score"
		doc.set("criteria", [{"criterion_label": label, "max_score": best, "guidance_text": guide} for label, best, guide in criteria])
		doc.flags.ignore_permissions = True
		doc.save()
