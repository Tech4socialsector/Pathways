import { callMethod } from './api'

// Candidates menu: one record per email address, with all their applications.
export const candidateService = {
  list() {
    return callMethod('pathways.api.candidates.list_candidates')
  },
  get(name) {
    return callMethod('pathways.api.candidates.get_candidate', { name })
  },
}
