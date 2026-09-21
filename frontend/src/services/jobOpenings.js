import { callMethod } from './api'

export const jobOpeningService = {
  getOpenJobs(params = {}) {
    return callMethod('pathways.api.application.get_open_job_openings', params)
  },
  getJobDetail(jobOpening) {
    return callMethod('pathways.api.application.get_job_opening_detail', { job_opening: jobOpening })
  },
}
