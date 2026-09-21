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
