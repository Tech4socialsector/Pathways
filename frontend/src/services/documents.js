import { callMethod } from './api'

export const documentService = {
  getMyDocumentChecklist(applicationName) {
    return callMethod('pathways.api.documents.get_my_document_checklist', {
      application_name: applicationName,
    })
  },
  uploadDocument(documentCollectionName, documentType, attachment) {
    return callMethod('pathways.api.documents.upload_document', {
      document_collection_name: documentCollectionName,
      document_type: documentType,
      attachment,
    })
  },
  verifyDocument(documentCollectionName, documentType, verified, rejectionReason) {
    return callMethod('pathways.api.documents.verify_document', {
      document_collection_name: documentCollectionName,
      document_type: documentType,
      verified,
      rejection_reason: rejectionReason,
    })
  },
  // Staff: Documents > Onboarding Verification
  listOnboardingCollections() {
    return callMethod('pathways.api.documents.list_onboarding_collections')
  },
  getCollection(name) {
    return callMethod('pathways.api.documents.get_collection', { name })
  },
  // Per new joiner: ask for one more document, or stop asking for one.
  addChecklistDocument(name, documentType, requirement) {
    return callMethod('pathways.api.documents.add_checklist_document', { name, document_type: documentType, requirement })
  },
  removeChecklistDocument(name, documentType) {
    return callMethod('pathways.api.documents.remove_checklist_document', { name, document_type: documentType })
  },
}
