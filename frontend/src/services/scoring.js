import { callMethod } from './api'

export const scoringService = {
  getApplicationForReview(application) {
    return callMethod('pathways.api.scoring.get_application_for_review', { application })
  },
  getRubricForJobOpening(jobOpening, stage) {
    return callMethod('pathways.api.scoring.get_rubric_for_job_opening', { job_opening: jobOpening, stage })
  },
  setEligibility(application, eligible, reason) {
    return callMethod('pathways.api.scoring.set_eligibility', { application, eligible: eligible ? 1 : 0, reason })
  },
  bulkSetEligibility(names, eligible, reason) {
    return callMethod('pathways.api.scoring.bulk_set_eligibility', { names, eligible: eligible ? 1 : 0, reason })
  },
  getCommitteeOptions() {
    return callMethod('pathways.api.scoring.get_committee_options')
  },
  createShortlistingCommittee(jobOpening, members, officeOrderReference) {
    return callMethod('pathways.api.scoring.create_shortlisting_committee', {
      job_opening: jobOpening,
      members,
      office_order_reference: officeOrderReference,
    })
  },
  submitShortlistingScore(data) {
    return callMethod('pathways.api.scoring.submit_shortlisting_score', data)
  },
  submitInterviewAssessment(data) {
    return callMethod('pathways.api.scoring.submit_interview_assessment', data)
  },
  consolidateScores(interview) {
    return callMethod('pathways.api.scoring.consolidate_scores', { interview })
  },
}
