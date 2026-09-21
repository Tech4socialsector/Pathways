import { ref } from 'vue'
import { jobOpeningService } from '@/services/jobOpenings'

export function useJobOpenings() {
  const jobs = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchJobs(params = {}) {
    loading.value = true
    error.value = null
    try {
      jobs.value = await jobOpeningService.getOpenJobs(params)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { jobs, loading, error, fetchJobs }
}

export function useJobOpeningDetail() {
  const job = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchJob(jobOpening) {
    loading.value = true
    error.value = null
    try {
      job.value = await jobOpeningService.getJobDetail(jobOpening)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { job, loading, error, fetchJob }
}

// Staff-facing variants — internal /jobs pages, all statuses, backed by
// pathways.api.job_opening (not the public job-board endpoints above).
export function useStaffJobOpenings() {
  const jobs = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchJobs(filters = {}, params = {}) {
    loading.value = true
    error.value = null
    try {
      jobs.value = await jobOpeningService.listStaffJobs(filters, params)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { jobs, loading, error, fetchJobs }
}

export function useStaffJobOpeningDetail() {
  const job = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const permissions = ref({ can_write: false, can_delete: false })

  async function fetchJob(jobOpening) {
    loading.value = true
    error.value = null
    try {
      job.value = await jobOpeningService.getStaffJobDetail(jobOpening)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  async function fetchPermissions(jobOpening) {
    try {
      permissions.value = await jobOpeningService.getJobPermissions(jobOpening)
    } catch (e) {
      permissions.value = { can_write: false, can_delete: false }
    }
  }

  return { job, loading, error, permissions, fetchJob, fetchPermissions }
}
