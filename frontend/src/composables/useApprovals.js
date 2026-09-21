import { ref } from 'vue'
import { approvalService } from '@/services/approvals'

export function usePendingApprovals() {
  const approvals = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchApprovals() {
    loading.value = true
    error.value = null
    try {
      approvals.value = await approvalService.getMyPendingApprovals()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  async function act(doctype, docname, action, remarks, channel) {
    await approvalService.recordApprovalAction(doctype, docname, action, remarks, channel)
    await fetchApprovals()
  }

  return { approvals, loading, error, fetchApprovals, act }
}

export function useApprovalChain() {
  const chain = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchChain(doctype, docname) {
    loading.value = true
    error.value = null
    try {
      chain.value = await approvalService.getApprovalChainStatus(doctype, docname)
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }

  return { chain, loading, error, fetchChain }
}
