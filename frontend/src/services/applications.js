import { callMethod } from './api'

export const applicationService = {
  submitApplication(jobOpening, data) {
    return callMethod('pathways.api.application.submit_application', { job_opening: jobOpening, data })
  },
  registerCandidate(email, fullName, redirectTo) {
    return callMethod('pathways.api.auth.register_candidate', {
      email,
      full_name: fullName,
      redirect_to: redirectTo,
    })
  },
  getApplicationDetail(applicationName) {
    return callMethod('pathways.api.application.get_application_detail', { application_name: applicationName })
  },
  getMyApplications() {
    return callMethod('pathways.api.application.get_my_applications')
  },
  getApplicationStatus(applicationName) {
    return callMethod('pathways.api.application.get_application_status', {
      application_name: applicationName,
    })
  },
  withdrawApplication(applicationName) {
    return callMethod('pathways.api.application.withdraw_application', {
      application_name: applicationName,
    })
  },
  deleteApplication(application) {
    return callMethod('pathways.api.application.delete_application', { application })
  },
}
