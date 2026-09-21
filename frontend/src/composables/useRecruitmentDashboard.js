import { ref } from 'vue'
import { reportService } from '@/services/reports'

export function useAdminDashboard() {
  const summary = ref(null)
  const funnel = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchSummary(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const [summaryResult, funnelResult] = await Promise.all([
        reportService.getAdminSummary(filters),
        reportService.getPipelineFunnel(filters),
      ])
      summary.value = summaryResult
      funnel.value = funnelResult
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { summary, funnel, loading, error, fetchSummary }
}

export function useRecruiterDashboard() {
  const summary = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchSummary() {
    loading.value = true
    error.value = null
    try {
      summary.value = await reportService.getRecruiterSummary()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { summary, loading, error, fetchSummary }
}
