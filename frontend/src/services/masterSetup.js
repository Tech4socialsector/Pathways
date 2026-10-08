import { callMethod } from './api'

export const masterSetupService = {
  hasAccess() {
    return callMethod('pathways.api.master_setup.has_access')
  },
  getMasterSetup() {
    return callMethod('pathways.api.master_setup.get_master_setup')
  },
  getMasterRecords(doctype, limit = 8) {
    return callMethod('pathways.api.master_setup.get_master_records', { doctype, limit })
  },
  getPosition(name) {
    return callMethod('frappe.client.get', { doctype: 'Position', name })
  },
}
