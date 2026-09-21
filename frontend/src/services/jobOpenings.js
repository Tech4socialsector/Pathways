import { callMethod } from './api'

export const jobOpeningService = {
  // Public job board (guests/candidates) — status is hardcoded server-side
  // to Advertised. Do not point staff-facing UI at these.
  getOpenJobs(params = {}) {
    return callMethod('pathways.api.application.get_open_job_openings', params)
  },
  getJobDetail(jobOpening) {
    return callMethod('pathways.api.application.get_job_opening_detail', { job_opening: jobOpening })
  },

  // Staff-facing (internal /jobs pages) — all statuses, scoped only by
  // the user's real Job Opening Role Permissions.
  listStaffJobs(filters = {}, params = {}) {
    return callMethod('pathways.api.job_opening.list_job_openings', { filters, ...params })
  },
  getStaffJobDetail(jobOpening) {
    return callMethod('pathways.api.job_opening.get_job_opening', { job_opening: jobOpening })
  },
  getJobPermissions(jobOpening) {
    return callMethod('pathways.api.job_opening.get_job_opening_permissions', { job_opening: jobOpening })
  },
  createJob(data) {
    return callMethod('pathways.api.job_opening.create_job_opening', { data })
  },
  updateJob(jobOpening, data) {
    return callMethod('pathways.api.job_opening.update_job_opening', { job_opening: jobOpening, data })
  },
  deleteJob(jobOpening) {
    return callMethod('pathways.api.job_opening.delete_job_opening', { job_opening: jobOpening })
  },
}
