import { ref } from 'vue'
import { masterSetupService } from '@/services/masterSetup'

// Shared across the sidebar and page so access is checked once per load.
const canAccess = ref(false)
let accessPromise = null

export function useMasterSetupAccess() {
  function fetchAccess() {
    if (!accessPromise) {
      accessPromise = masterSetupService
        .hasAccess()
        .then((value) => {
          canAccess.value = !!value
        })
        .catch(() => {
          canAccess.value = false
          accessPromise = null
        })
    }
    return accessPromise
  }

  return { canAccess, fetchAccess }
}

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
