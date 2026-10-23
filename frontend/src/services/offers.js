import { callMethod, downloadMethod } from './api'

const M = 'pathways.api.offer.'

export const offerService = {
  // ----- staff
  getOffers() {
    return callMethod(M + 'get_offers')
  },
  getOfferCandidates() {
    return callMethod(M + 'get_offer_candidates')
  },
  getOfferForApplication(application) {
    return callMethod(M + 'get_offer_for_application', { application })
  },
  getFormOptions() {
    return callMethod(M + 'get_form_options')
  },
  getTemplates() {
    return callMethod(M + 'get_templates')
  },
  createOffer(application, data = {}) {
    return callMethod(M + 'create_offer', { application, data })
  },
  getOffer(name) {
    return callMethod(M + 'get_offer', { name })
  },
  updateOffer(name, data) {
    return callMethod(M + 'update_offer', { name, data })
  },
  submitForReview(name) {
    return callMethod(M + 'submit_for_review', { name })
  },
  approveOffer(name, remarks) {
    return callMethod(M + 'approve_offer', { name, remarks })
  },
  returnOffer(name, remarks) {
    return callMethod(M + 'return_offer', { name, remarks })
  },
  signOffer(name, { signature = null, useSavedSignature = false, saveAsDefault = false } = {}) {
    return callMethod(M + 'sign_offer', {
      name,
      signature,
      use_saved_signature: useSavedSignature ? 1 : 0,
      save_as_default: saveAsDefault ? 1 : 0,
    })
  },
  sendOffer(name, acceptanceDeadline) {
    return callMethod(M + 'send_offer', { name, acceptance_deadline: acceptanceDeadline || null })
  },
  uploadRegistrarScan(name, fileUrl) {
    return callMethod(M + 'upload_registrar_scan', { name, file_url: fileUrl })
  },
  deleteOffer(name) {
    return callMethod(M + 'delete_offer', { name })
  },
  previewLetter(name) {
    return callMethod(M + 'preview_letter', { name })
  },
  downloadLetter(name) {
    return downloadMethod(M + 'download_letter', { name }, `Appointment Order - ${name}.pdf`)
  },

  // ----- candidate
  getMyOffer(applicationName) {
    return callMethod(M + 'get_my_offer', { application_name: applicationName })
  },
  respondToOffer(offerName, response, confirmedDoj, signedCopyAttachment, declineReason) {
    return callMethod(M + 'respond_to_offer', {
      offer_name: offerName,
      response,
      confirmed_doj: confirmedDoj,
      signed_copy_attachment: signedCopyAttachment,
      decline_reason: declineReason,
    })
  },
  uploadSignedCopy(name, fileUrl) {
    return callMethod(M + 'upload_signed_copy', { name, file_url: fileUrl })
  },
}
