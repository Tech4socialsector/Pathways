import { callMethod, downloadMethod } from './api'

// Interview panel: Selection Committee members score final interviews on
// the Interview Assessment Form (workflow folder "6. Final Interview").
export const panelService = {
  getMyPanel() {
    return callMethod('pathways.api.panel.get_my_panel')
  },
  // panelist: the recruitment team typing in that panellist's form
  getAssessmentForm(interview, panelist = null) {
    return callMethod('pathways.api.panel.get_assessment_form', { interview, panelist })
  },
  getConsolidated(jobOpening, interviewDate = '') {
    return callMethod('pathways.api.panel.get_consolidated', { job_opening: jobOpening, interview_date: interviewDate || null })
  },
  setOutcome(applications, outcome) {
    return callMethod('pathways.api.panel.set_selection_outcome', { applications: JSON.stringify(applications), outcome })
  },
  exportConsolidated(jobOpening, jobTitle, interviewDate = '') {
    return downloadMethod('pathways.api.panel.export_consolidated', { job_opening: jobOpening, interview_date: interviewDate || null }, `Consolidated Score Sheet - ${jobTitle}.xlsx`)
  },
  downloadForms(jobOpening, jobTitle, panelist = null, interviewDate = '', blank = false) {
    return downloadMethod(
      'pathways.api.panel.download_assessment_forms',
      { job_opening: jobOpening, panelist, interview_date: interviewDate || null, blank: blank ? 1 : 0 },
      `Interview Assessment Form - ${jobTitle}.pdf`,
    )
  },
  // Job-level files for the panel (workflow step 16)
  getJobShareOptions(jobOpening) {
    return callMethod('pathways.api.panel_documents.get_job_share_options', { job_opening: jobOpening })
  },
  // changes: { panelist: { fileLabel: true | false } }
  shareJobFiles(jobOpening, changes, note = '', notify = true) {
    return callMethod('pathways.api.panel_documents.share_job_files', {
      job_opening: jobOpening,
      changes: JSON.stringify(changes),
      note,
      notify: notify ? 1 : 0,
    })
  },
  downloadJobFile(jobOpening, label) {
    return downloadMethod('pathways.api.panel_documents.download_job_file', { job_opening: jobOpening, label }, `${label}.pdf`)
  },
  // Documents page > Share with panel
  getShareOptions(applications) {
    return callMethod('pathways.api.panel_documents.get_share_options', { applications: JSON.stringify(applications) })
  },
  // changes: { panelist: { documentLabel: true (share) | false (stop sharing) } }
  shareWithPanel(applications, changes, note = '', notify = true) {
    return callMethod('pathways.api.panel_documents.share_with_panel', {
      applications: JSON.stringify(applications),
      changes: JSON.stringify(changes),
      note,
      notify: notify ? 1 : 0,
    })
  },
  getSharedDocuments(jobOpening = '') {
    return callMethod('pathways.api.panel_documents.get_shared_documents', { job_opening: jobOpening || null })
  },
  // Round 1 (HR): hrOutcome, expectedSalary, noticePeriod; signature: data URL
  submitAssessment({ interview, panelist, scores, verdict, additionalComments, areaOfSpecialization, hrOutcome, expectedSalary, noticePeriod, signature }) {
    return callMethod('pathways.api.panel.submit_assessment', {
      interview,
      panelist: panelist || null,
      scores: JSON.stringify(scores),
      verdict: verdict || null,
      additional_comments: additionalComments || '',
      area_of_specialization: areaOfSpecialization || '',
      hr_outcome: hrOutcome || null,
      expected_salary: expectedSalary || '',
      notice_period: noticePeriod || '',
      signature: signature || null,
    })
  },
}
