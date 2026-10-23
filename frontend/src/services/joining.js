import { callMethod } from './api'

// Joinings (workflow step 31) and IT & Facilities requests (folder 12).
export const joiningService = {
  listJoinings() {
    return callMethod('pathways.api.joining.list_joinings')
  },
  getJoining(name) {
    return callMethod('pathways.api.joining.get_joining', { name })
  },
  saveJoining(name, values) {
    return callMethod('pathways.api.joining.save_joining', { name, values })
  },
  setStatus(name, status, values = null) {
    return callMethod('pathways.api.joining.set_status', { name, status, values })
  },
  startOnboarding(offer) {
    return callMethod('pathways.api.joining.start_onboarding', { offer })
  },
}

export const itRequestService = {
  listRequests() {
    return callMethod('pathways.api.it_requests.list_requests')
  },
  saveRequest(name, values, complete = false) {
    return callMethod('pathways.api.it_requests.save_request', { name, values, complete })
  },
}
