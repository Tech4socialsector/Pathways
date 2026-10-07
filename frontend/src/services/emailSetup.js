import { callMethod } from './api'

export const emailSetupService = {
  getSetup() {
    return callMethod('pathways.api.email_setup.get_email_setup')
  },
  saveAccount(data) {
    return callMethod('pathways.api.email_setup.save_email_account', { data })
  },
  sendTest(recipient) {
    return callMethod('pathways.api.email_setup.send_test_email', { recipient })
  },
  saveRule(event, data) {
    return callMethod('pathways.api.email_setup.save_email_rule', { event, data })
  },
  removeAttachment(event, file) {
    return callMethod('pathways.api.email_setup.remove_rule_attachment', { event, file })
  },
  createTemplate(name, subject, response) {
    return callMethod('pathways.api.email_setup.create_email_template', { name, subject, response })
  },
  previewRule(event) {
    return callMethod('pathways.api.email_setup.preview_email_rule', { event })
  },
  deleteRule(event) {
    return callMethod('pathways.api.email_setup.delete_email_rule', { event })
  },
  toggleRule(event, enabled) {
    return callMethod('pathways.api.email_setup.toggle_email_rule', { event, enabled })
  },
}
