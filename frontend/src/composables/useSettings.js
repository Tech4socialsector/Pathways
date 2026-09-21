import { ref } from 'vue'
import { settingsService } from '@/services/settings'

export function useSettings() {
  const settings = ref(null)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref(null)

  async function fetchSettings() {
    loading.value = true
    error.value = null
    try {
      settings.value = await settingsService.getSettings()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  async function saveSettings(data) {
    saving.value = true
    error.value = null
    try {
      settings.value = await settingsService.updateSettings(data)
      return true
    } catch (e) {
      error.value = e
      return false
    } finally {
      saving.value = false
    }
  }

  return { settings, loading, saving, error, fetchSettings, saveSettings }
}
