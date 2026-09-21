import { ref } from 'vue'
import { documentService } from '@/services/documents'

export function useDocumentChecklist() {
  const checklist = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchChecklist(applicationName) {
    loading.value = true
    error.value = null
    try {
      checklist.value = await documentService.getMyDocumentChecklist(applicationName)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  async function upload(documentCollectionName, documentType, attachment, applicationName) {
    await documentService.uploadDocument(documentCollectionName, documentType, attachment)
    await fetchChecklist(applicationName)
  }

  return { checklist, loading, error, fetchChecklist, upload }
}
