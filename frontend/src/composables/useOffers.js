import { ref } from 'vue'
import { offerService } from '@/services/offers'

export function useMyOffer() {
  const offer = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchOffer(applicationName) {
    loading.value = true
    error.value = null
    try {
      offer.value = await offerService.getMyOffer(applicationName)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  async function respond(offerName, response, confirmedDoj, signedCopyAttachment) {
    await offerService.respondToOffer(offerName, response, confirmedDoj, signedCopyAttachment)
  }

  return { offer, loading, error, fetchOffer, respond }
}
