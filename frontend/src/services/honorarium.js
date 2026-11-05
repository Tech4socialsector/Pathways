import { callMethod, downloadMethod } from './api'

// Panel thank-you and honorarium for external experts (workflow step 33).
export const honorariumService = {
  sendPanelThanks(jobOpening) {
    return callMethod('pathways.api.honorarium.send_panel_thanks', { job_opening: jobOpening })
  },
  syncExternalPanellists() {
    return callMethod('pathways.api.honorarium.sync_external_panellists')
  },
  list(jobOpening = '', status = '') {
    return callMethod('pathways.api.honorarium.get_honoraria', { job_opening: jobOpening || null, status: status || null })
  },
  // fields: amount, pan_number, account_holder_name, bank_account_number, bank_name,
  // bank_branch, ifsc_code, pan_card_copy, bank_consent_form, supporting_document, remarks
  update(name, fields) {
    return callMethod('pathways.api.honorarium.update_honorarium', { name, ...fields })
  },
  previewFinanceEmail(name) {
    return callMethod('pathways.api.honorarium.preview_finance_email', { name })
  },
  // addresses: { to, cc, bcc, remember } as edited in the preview
  sendToFinance(names, addresses = {}) {
    return callMethod('pathways.api.honorarium.send_to_finance', { names: JSON.stringify(names), ...addresses })
  },
  exportList(jobOpening = '', status = '') {
    return downloadMethod('pathways.api.honorarium.export_honoraria', { job_opening: jobOpening || null, status: status || null }, 'Panel Honorarium.xlsx')
  },
}
