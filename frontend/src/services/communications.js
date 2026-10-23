import { callMethod } from './api'

export const communicationService = {
  // filters: { event, job_opening, application, status, recipient, from_date, to_date }
  list(filters = {}, start = 0, pageLength = 500) {
    return callMethod('pathways.api.communications.list_communications', { filters, start, page_length: pageLength })
  },
  getFilterOptions() {
    return callMethod('pathways.api.communications.get_filter_options')
  },
  get(name) {
    return callMethod('pathways.api.communications.get_communication', { name })
  },
  listForApplication(application) {
    return callMethod('pathways.api.communications.list_for_application', { application })
  },
}
