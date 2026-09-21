import { callMethod } from './api'

export const applicationService = {
  checkDuplicate(email, mobileNumber, jobOpening) {
    return callMethod('pathways.api.application.check_duplicate', {
      email,
      mobile_number: mobileNumber,
      job_opening: jobOpening,
    })
  },
  submitApplication(candidateData, applicationData) {
    return callMethod('pathways.api.application.submit_application', {
      candidate_data: candidateData,
      application_data: applicationData,
    })
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
}
