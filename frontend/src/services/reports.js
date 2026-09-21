import { callMethod } from './api'

export const reportService = {
  getAdminSummary(params = {}) {
    return callMethod('pathways.api.dashboard.get_admin_summary', params)
  },
  getRecruiterSummary() {
    return callMethod('pathways.api.dashboard.get_recruiter_summary')
  },
}
