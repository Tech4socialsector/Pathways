import { callMethod } from './api'

// After the final interview (workflow steps 32-33), from the consolidated
// score sheet: regrets to candidates not selected.
export const selectionService = {
  // { regret: { not_selected, waitlisted, waitlist_released, sent, enabled }, thanks: {...} }
  getPostInterviewSummary(jobOpening) {
    return callMethod('pathways.api.selection.get_post_interview_summary', { job_opening: jobOpening })
  },
  sendRegrets(jobOpening, includeWaitlisted = false) {
    return callMethod('pathways.api.selection.send_post_interview_regrets', {
      job_opening: jobOpening,
      include_waitlisted: includeWaitlisted ? 1 : 0,
    })
  },
}
