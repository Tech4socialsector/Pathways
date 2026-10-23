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
  // extra: { shortlisting_deadline, office_order_attachment }
  createShortlistingCommittee(jobOpening, members, officeOrderReference, extra = {}) {
    return callMethod('pathways.api.scoring.create_shortlisting_committee', {
      job_opening: jobOpening,
      members,
      office_order_reference: officeOrderReference,
      ...extra,
    })
  },
  getShortlistingCommittee(jobOpening) {
    return callMethod('pathways.api.scoring.get_shortlisting_committee', { job_opening: jobOpening })
  },
  updateShortlistingCommittee(jobOpening, data) {
    return callMethod('pathways.api.scoring.update_shortlisting_committee', { job_opening: jobOpening, ...data })
  },
  getShortlistingReport(jobOpening) {
    return callMethod('pathways.api.shortlisting_report.get_shortlisting_report', { job_opening: jobOpening })
  },
  shortlistingReportUrl(jobOpening) {
    return `/api/method/pathways.api.shortlisting_report.download_shortlisting_report?job_opening=${encodeURIComponent(jobOpening)}`
  },
  sendRegretEmails(jobOpening, groups) {
    return callMethod('pathways.api.scoring.send_regret_emails', { job_opening: jobOpening, groups })
  },
  submitShortlistingScore(data) {
    return callMethod('pathways.api.scoring.submit_shortlisting_score', data)
  },
}
