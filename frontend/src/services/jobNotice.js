import { callMethod } from './api'

export const jobNoticeService = {
  getNotice(jobOpening) {
    return callMethod('pathways.api.job_notice.get_job_notice', { job_opening: jobOpening })
  },
  saveNotice(jobOpening, data) {
    return callMethod('pathways.api.job_notice.save_job_notice', { job_opening: jobOpening, data })
  },
  issueCorrigendum(jobOpening, data) {
    return callMethod('pathways.api.job_notice.issue_corrigendum', { job_opening: jobOpening, ...data })
  },
}
