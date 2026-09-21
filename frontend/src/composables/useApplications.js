import { ref } from 'vue'
import { applicationService } from '@/services/applications'

export function useMyApplications() {
  const applications = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchApplications() {
    loading.value = true
    error.value = null
    try {
      applications.value = await applicationService.getMyApplications()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { applications, loading, error, fetchApplications }
}

export function useApplicationStatus() {
  const status = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchStatus(applicationName) {
    loading.value = true
    error.value = null
    try {
      status.value = await applicationService.getApplicationStatus(applicationName)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  async function withdraw(applicationName) {
    await applicationService.withdrawApplication(applicationName)
    await fetchStatus(applicationName)
  }

  return { status, loading, error, fetchStatus, withdraw }
}

export function useApplicationForm() {
  const submitting = ref(false)
  const error = ref(null)
  const result = ref(null)

  async function checkDuplicate(email, mobileNumber, jobOpening) {
    return applicationService.checkDuplicate(email, mobileNumber, jobOpening)
  }

  async function submit(candidateData, applicationData) {
    submitting.value = true
    error.value = null
    try {
      result.value = await applicationService.submitApplication(candidateData, applicationData)
      return result.value
    } catch (e) {
      error.value = e
      throw e
    } finally {
      submitting.value = false
    }
  }

  return { submitting, error, result, checkDuplicate, submit }
}
