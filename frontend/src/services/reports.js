import { callMethod } from './api'

export const reportService = {
  getAdminSummary(params = {}) {
    return callMethod('pathways.api.dashboard.get_admin_summary', params)
  },
  getPipelineFunnel(params = {}) {
    return callMethod('pathways.api.dashboard.get_pipeline_funnel', params)
  },
  getDrilldown(bucket, params = {}) {
    return callMethod('pathways.api.dashboard.get_drilldown', { bucket, ...params })
  },
  getRecruiterSummary() {
    return callMethod('pathways.api.dashboard.get_recruiter_summary')
  },
}
