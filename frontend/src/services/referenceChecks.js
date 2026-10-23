import { callMethod } from './api'

// Reference checks (workflow step 21): the staff References panel and the
// referee's public, token-based form.
const M = 'pathways.api.reference_checks'

export const referenceCheckService = {
  getApplicationChecks(application) {
    return callMethod(`${M}.get_application_checks`, { application })
  },
  createChecks(application, referees = null) {
    return callMethod(`${M}.create_checks`, { application, referees: referees ? JSON.stringify(referees) : null })
  },
  updateReferee(check, fields) {
    return callMethod(`${M}.update_referee`, { check, ...fields })
  },
  sendRequest(check) {
    return callMethod(`${M}.send_request`, { check })
  },
  recordResponses(check, answers, summary, complete = false) {
    return callMethod(`${M}.record_responses`, {
      check,
      answers: JSON.stringify(answers),
      overall_assessment_summary: summary ?? null,
      complete: complete ? 1 : 0,
    })
  },
  saveSummary(check, summary) {
    return callMethod(`${M}.save_summary`, { check, overall_assessment_summary: summary || '' })
  },
  summaryForApplications(names) {
    return callMethod(`${M}.summary_for_applications`, { names: JSON.stringify(names) })
  },
  printUrl(check) {
    return `/printview?doctype=${encodeURIComponent('Reference Check')}&name=${encodeURIComponent(check)}&format=${encodeURIComponent('Reference Check')}&no_letterhead=0`
  },

  // Referee (guest) endpoints
  getRefereeForm(token) {
    return callMethod(`${M}.get_referee_form`, { token })
  },
  submitRefereeForm(token, answers) {
    return callMethod(`${M}.submit_referee_form`, { token, answers: JSON.stringify(answers) })
  },
}
