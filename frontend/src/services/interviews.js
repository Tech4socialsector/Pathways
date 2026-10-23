import { callMethod, downloadMethod } from './api'

// Interview stage (workflow steps 13-16): Selection Committee, scheduling,
// invites and the candidate's RSVP.
export const interviewService = {
  getJobInterviews(jobOpening) {
    return callMethod('pathways.api.interviews.get_job_interviews', { job_opening: jobOpening })
  },
  getPanelOptions() {
    return callMethod('pathways.api.interviews.get_panel_options')
  },
  saveSelectionCommittee(jobOpening, members, scheduledDate, scheduledTime) {
    return callMethod('pathways.api.interviews.save_selection_committee', {
      job_opening: jobOpening,
      members,
      scheduled_date: scheduledDate || null,
      scheduled_time: scheduledTime || null,
    })
  },
  scheduleInterviews(params) {
    return callMethod('pathways.api.interviews.schedule_interviews', params)
  },
  resendInvite(interview) {
    return callMethod('pathways.api.interviews.resend_invite', { interview })
  },
  setStatus(interview, status, { reason = '', notify = 0, cc = [] } = {}) {
    return callMethod('pathways.api.interviews.set_interview_status', { interview, status, reason, notify, cc: JSON.stringify(cc) })
  },
  getEmailRecipients({ roundType, jobOpenings = [], cancelled = false } = {}) {
    return callMethod('pathways.api.interviews.get_email_recipients', {
      round_type: roundType,
      job_openings: JSON.stringify(jobOpenings),
      cancelled: cancelled ? 1 : 0,
    })
  },
  updateInterview(params) {
    return callMethod('pathways.api.interviews.update_interview', params)
  },
  respondRsvp(interview, response) {
    return callMethod('pathways.api.interviews.respond_rsvp', { interview, response })
  },
  getMeetStatus() {
    return callMethod('pathways.api.interviews.get_meet_status')
  },
  listToSchedule() {
    return callMethod('pathways.api.interviews.list_to_schedule')
  },
  listInterviews() {
    return callMethod('pathways.api.interviews.list_interviews')
  },
  // Workflow step 14: final shortlist and the job's Shortlisting Note
  setFinalShortlist(jobOpening, applications, shortlisted = true, remarks = null) {
    return callMethod('pathways.api.interviews.set_final_shortlist', {
      job_opening: jobOpening,
      applications: JSON.stringify(applications),
      shortlisted: shortlisted ? 1 : 0,
      remarks,
    })
  },
  getShortlistingNote(jobOpening) {
    return callMethod('pathways.api.interviews.get_shortlisting_note', { job_opening: jobOpening })
  },
  // attachments: [{ label, attachment }]; remarks: { application: text }
  saveShortlistingNote(jobOpening, { note, attachments, remarks } = {}) {
    return callMethod('pathways.api.interviews.save_shortlisting_note', {
      job_opening: jobOpening,
      note: note ?? null,
      attachments: attachments ? JSON.stringify(attachments) : null,
      remarks: remarks ? JSON.stringify(remarks) : null,
    })
  },
  downloadShortlistingNote(jobOpening, jobTitle) {
    return downloadMethod('pathways.api.interviews.download_shortlisting_note', { job_opening: jobOpening }, `Shortlisting Note - ${jobTitle}.pdf`)
  },
  getHrInteraction(application) {
    return callMethod('pathways.api.interviews.get_hr_interaction', { application })
  },
  // Workflow step 16: the day's running order, Excel or PDF
  exportSchedule(jobOpening, jobTitle, { roundType = 'Final', interviewDate = '', format = 'xlsx' } = {}) {
    return downloadMethod(
      'pathways.api.interviews.export_interview_schedule',
      { job_opening: jobOpening, round_type: roundType, interview_date: interviewDate || null, file_format: format },
      `Interview Schedule - ${jobTitle}.${format}`,
    )
  },
}
