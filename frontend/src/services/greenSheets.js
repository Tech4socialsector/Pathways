import { callMethod } from './api'

// Pre-Recruitment Green Sheet actions for the staff Job Opening page.
// Approve/Return goes through approvalService.recordApprovalAction.
export const greenSheetService = {
  getJobGreenSheets(jobOpening) {
    return callMethod('pathways.api.green_sheet.get_job_green_sheets', { job_opening: jobOpening })
  },
  saveGreenSheet(jobOpening, data, { name = null, submit = false } = {}) {
    return callMethod('pathways.api.green_sheet.save_green_sheet', {
      job_opening: jobOpening,
      justification_note: data.justification_note,
      duration_of_ad_days: data.duration_of_ad_days,
      jd_attachment: data.jd_attachment || null,
      supporting_attachment: data.supporting_attachment || null,
      name,
      submit: submit ? 1 : 0,
    })
  },
  submitGreenSheet(name) {
    return callMethod('pathways.api.green_sheet.submit_green_sheet', { name })
  },
  withdrawGreenSheet(name) {
    return callMethod('pathways.api.green_sheet.withdraw_green_sheet', { name })
  },
  reviseGreenSheet(name) {
    return callMethod('pathways.api.green_sheet.revise_green_sheet', { name })
  },
  deleteGreenSheetDraft(name) {
    return callMethod('pathways.api.green_sheet.delete_green_sheet_draft', { name })
  },
  attachSignedCopy(name, fileUrl) {
    return callMethod('pathways.api.green_sheet.attach_signed_green_sheet', { name, file_url: fileUrl })
  },
}
