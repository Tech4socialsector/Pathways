import { callMethod } from './api'

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
  setStatus(interview, status) {
    return callMethod('pathways.api.interviews.set_interview_status', { interview, status })
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
}
