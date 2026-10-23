import { callMethod } from './api'

export const POST_GREEN_SHEET_DOCTYPE = 'Post-Interview Green Sheet'

// Post-Interview ("selection") Green Sheet: raised from the job page or the
// consolidated score sheet, edited on /selection-green-sheets/:id.
// Approve/Return goes through approvalService.recordApprovalAction.
export const postGreenSheetService = {
  getJobSelection(jobOpening) {
    return callMethod('pathways.api.post_green_sheet.get_job_selection', { job_opening: jobOpening })
  },
  getSheet(name) {
    return callMethod('pathways.api.post_green_sheet.get_sheet', { name })
  },
  createFromOutcomes(jobOpening) {
    return callMethod('pathways.api.post_green_sheet.create_from_outcomes', { job_opening: jobOpening })
  },
  refreshFromOutcomes(name) {
    return callMethod('pathways.api.post_green_sheet.refresh_from_outcomes', { name })
  },
  saveSheet(name, data, { submit = false } = {}) {
    return callMethod('pathways.api.post_green_sheet.save_sheet', { name, data, submit: submit ? 1 : 0 })
  },
  submitSheet(name) {
    return callMethod('pathways.api.post_green_sheet.submit_sheet', { name })
  },
  withdrawSheet(name) {
    return callMethod('pathways.api.post_green_sheet.withdraw_sheet', { name })
  },
  reviseSheet(name) {
    return callMethod('pathways.api.post_green_sheet.revise_sheet', { name })
  },
  deleteDraft(name) {
    return callMethod('pathways.api.post_green_sheet.delete_draft', { name })
  },
  attachSignedCopy(name, fileUrl) {
    return callMethod('pathways.api.post_green_sheet.attach_signed_copy', { name, file_url: fileUrl })
  },
}

/** Desk print view of a sheet in one of its print formats. */
export function printUrl(name, format = 'Post-Interview Green Sheet') {
  const q = new URLSearchParams({ doctype: POST_GREEN_SHEET_DOCTYPE, name, format, no_letterhead: '0' })
  return `/printview?${q.toString()}`
}
