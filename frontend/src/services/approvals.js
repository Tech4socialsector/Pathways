import { callMethod } from './api'

export const approvalService = {
  getMyPendingApprovals() {
    return callMethod('pathways.api.approval.get_my_pending_approvals')
  },
  recordApprovalAction(doctype, docname, action, remarks, channel = 'Digital') {
    return callMethod('pathways.api.approval.record_approval_action', {
      doctype,
      docname,
      action,
      remarks,
      channel,
    })
  },
  getApprovalChainStatus(doctype, docname) {
    return callMethod('pathways.api.approval.get_approval_chain_status', { doctype, docname })
  },
}
