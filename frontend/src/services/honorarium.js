import { callMethod, downloadMethod } from './api'

// Panel thank-you and honorarium (workflow step 33).
export const honorariumService = {
  sendPanelThanks(jobOpening) {
    return callMethod('pathways.api.honorarium.send_panel_thanks', { job_opening: jobOpening })
  },
  list(jobOpening = '', status = '') {
    return callMethod('pathways.api.honorarium.get_honoraria', { job_opening: jobOpening || null, status: status || null })
  },
  approve(names) {
    return callMethod('pathways.api.honorarium.approve', { names: JSON.stringify(names) })
  },
  markPaid(names, paidOn, paymentReference) {
    return callMethod('pathways.api.honorarium.mark_paid', {
      names: JSON.stringify(names),
      paid_on: paidOn || null,
      payment_reference: paymentReference || null,
    })
  },
  // fields: { amount, pan_number, bank_consent_form, remarks, not_applicable }
  update(name, fields) {
    return callMethod('pathways.api.honorarium.update_honorarium', { name, ...fields })
  },
  exportList(jobOpening = '', status = '') {
    return downloadMethod('pathways.api.honorarium.export_honoraria', { job_opening: jobOpening || null, status: status || null }, 'Panel Honorarium.xlsx')
  },
}
