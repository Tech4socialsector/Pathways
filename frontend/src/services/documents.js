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
}
