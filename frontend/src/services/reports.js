import { callMethod, downloadMethod } from './api'

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
  // Reports page: every chart for { track, job_opening, from_date, to_date }.
  getReportCharts(params = {}) {
    return callMethod('pathways.api.reports.get_report_charts', params)
  },
  exportReport(params = {}) {
    return downloadMethod('pathways.api.reports.export_report', params, 'recruitment-report.xlsx')
  },
  getRecruiterSummary() {
    return callMethod('pathways.api.dashboard.get_recruiter_summary')
  },
}
