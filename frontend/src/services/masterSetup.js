import { callMethod } from './api'

const API = 'pathways.api.master_setup'

export const masterSetupService = {
  hasAccess() {
    return callMethod(`${API}.has_access`)
  },
  getMasterSetup() {
    return callMethod(`${API}.get_master_setup`)
  },
  getMasterRecords(doctype, limit = 8) {
    return callMethod(`${API}.get_master_records`, { doctype, limit })
  },
  getPosition(name) {
    return callMethod('frappe.client.get', { doctype: 'Position', name })
  },

  // In-app list and form
  getForm(doctype) {
    return callMethod(`${API}.get_master_form`, { doctype })
  },
  getList(doctype, { txt = '', status = '', start = 0, pageLength = 20 } = {}) {
    return callMethod(`${API}.get_master_list`, { doctype, txt, status, start, page_length: pageLength })
  },
  getDoc(doctype, name) {
    return callMethod(`${API}.get_master_doc`, { doctype, name })
  },
  save(doctype, doc) {
    return callMethod(`${API}.save_master`, { doctype, doc })
  },
  remove(doctype, name) {
    return callMethod(`${API}.delete_master`, { doctype, name })
  },
  searchLink(doctype, txt = '') {
    return callMethod(`${API}.search_link`, { doctype, txt })
  },
  getValue(doctype, name, fieldname) {
    return callMethod('frappe.client.get_value', { doctype, filters: name, fieldname })
  },
}
