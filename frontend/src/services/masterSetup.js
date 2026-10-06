import { callMethod } from './api'

export const masterSetupService = {
  hasAccess() {
    return callMethod('pathways.api.master_setup.has_access')
  },
  getMasterSetup() {
    return callMethod('pathways.api.master_setup.get_master_setup')
  },
}
