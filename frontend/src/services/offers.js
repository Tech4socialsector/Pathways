import { callMethod } from './api'

export const offerService = {
  getMyOffer(applicationName) {
    return callMethod('pathways.api.offer.get_my_offer', { application_name: applicationName })
  },
  respondToOffer(offerName, response, confirmedDoj, signedCopyAttachment) {
    return callMethod('pathways.api.offer.respond_to_offer', {
      offer_name: offerName,
      response,
      confirmed_doj: confirmedDoj,
      signed_copy_attachment: signedCopyAttachment,
    })
  },
}
