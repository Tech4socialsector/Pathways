import { callMethod } from './api'

export const settingsService = {
  getSettings() {
    return callMethod('pathways.api.settings.get_settings')
  },
  updateSettings(data) {
    return callMethod('pathways.api.settings.update_settings', { data })
  },
  getGoogleSettings() {
    return callMethod('pathways.api.google_settings.get_google_settings')
  },
  saveGoogleSettings(data) {
    return callMethod('pathways.api.google_settings.save_google_settings', { data })
  },
}
