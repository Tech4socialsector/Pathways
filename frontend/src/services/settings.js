import { callMethod } from './api'

export const settingsService = {
  getSettings() {
    return callMethod('pathways.api.settings.get_settings')
  },
  updateSettings(data) {
    return callMethod('pathways.api.settings.update_settings', { data })
  },
}
