import { callMethod } from './api'

// The Selection module (after the final interviews): per-job progress,
// regrets to candidates not selected (step 32).
export const selectionService = {
  listJobs() {
    return callMethod('pathways.api.selection.list_selection_jobs')
  },
  getJob(jobOpening) {
    return callMethod('pathways.api.selection.get_selection_job', { job_opening: jobOpening })
  },
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
