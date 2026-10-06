import { ref } from 'vue'
import { masterSetupService } from '@/services/masterSetup'

export function useMasterSetup() {
  const categories = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchMasterSetup() {
    loading.value = true
    error.value = null
    try {
      categories.value = (await masterSetupService.getMasterSetup()) || []
    } catch (e) {
      error.value = e
      categories.value = []
    } finally {
      loading.value = false
    }
  }

  return { categories, loading, error, fetchMasterSetup }
}
