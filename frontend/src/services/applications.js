import { callMethod } from './api'

export const applicationService = {
  // Not via callMethod: frappe-ui's call() drops the response's
  // field_errors ({ field: message }), which the apply form shows per field.
  async submitApplication(jobOpening, data) {
    const headers = { Accept: 'application/json', 'Content-Type': 'application/json; charset=utf-8' }
    if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') headers['X-Frappe-CSRF-Token'] = window.csrf_token
    const res = await fetch('/api/method/pathways.api.application.submit_application', {
      method: 'POST',
      headers,
      body: JSON.stringify({ job_opening: jobOpening, data }),
    })
    const body = await res.json().catch(() => ({}))
    if (res.ok) return body.message
    const error = new Error('submit_application failed')
    error.status = res.status
    error.fieldErrors = body.field_errors || {}
    error.messages = serverMessages(body)
    throw error
  },
  registerCandidate(email, fullName, redirectTo) {
    return callMethod('pathways.api.auth.register_candidate', {
      email,
      full_name: fullName,
      redirect_to: redirectTo,
    })
  },
  bulkSetStatus(names, status, remarks) {
    return callMethod('pathways.api.application.bulk_set_application_status', { names, status, remarks })
  },
  // Full applications as an .xlsx: mode 'single' (one sheet) or
  // 'job_wise' (a sheet per job opening). POST, as the names list can be
  // long; saved through a blob link.
  async exportApplications(names, mode) {
    const headers = { 'Content-Type': 'application/json; charset=utf-8' }
    if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') headers['X-Frappe-CSRF-Token'] = window.csrf_token
    const res = await fetch('/api/method/pathways.api.application.export_applications', {
      method: 'POST',
      headers,
      body: JSON.stringify({ names, mode }),
    })
    if (!res.ok) {
      const error = new Error('export_applications failed')
      error.messages = serverMessages(await res.json().catch(() => ({})))
      throw error
    }
    const blob = await res.blob()
    const disposition = res.headers.get('Content-Disposition') || ''
    const fileName = /filename="?([^";]+)"?/.exec(disposition)?.[1] || `applications-${mode}.xlsx`
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    link.remove()
    // Revoke later: some browsers start the download after click() returns.
    setTimeout(() => URL.revokeObjectURL(link.href), 10000)
  },
  bulkDelete(names) {
    return callMethod('pathways.api.application.bulk_delete_applications', { names })
  },
  listApplicationDocuments() {
    return callMethod('pathways.api.application.list_application_documents')
  },
  getApplicationDocuments(applicationName) {
    return callMethod('pathways.api.application.get_application_documents', { application_name: applicationName })
  },
  // GET download: documents ZIP, one folder per document type.
  documentsZipUrl({ jobOpening, scope = 'all', applications } = {}) {
    const params = new URLSearchParams()
    if (applications) params.set('applications', JSON.stringify(applications))
    else {
      params.set('job_opening', jobOpening)
      params.set('scope', scope)
    }
    return `/api/method/pathways.api.application.download_documents_zip?${params}`
  },
  // GET download of every document merged into one PDF.
  downloadAllDocumentsUrl(applicationName) {
    return `/api/method/pathways.api.application.download_application_documents?application_name=${encodeURIComponent(applicationName)}`
  },
  getApplicationDetail(applicationName) {
    return callMethod('pathways.api.application.get_application_detail', { application_name: applicationName })
  },
  getStatusOptions(applicationName) {
    return callMethod('pathways.api.application.get_application_status_options', { application_name: applicationName })
  },
  setStatus(applicationName, status, remarks) {
    return callMethod('pathways.api.application.set_application_status', {
      application_name: applicationName,
      status,
      remarks,
    })
  },
  getMyApplications() {
    return callMethod('pathways.api.application.get_my_applications')
  },
  getApplicationStatus(applicationName) {
    return callMethod('pathways.api.application.get_application_status', {
      application_name: applicationName,
    })
  },
  withdrawApplication(applicationName) {
    return callMethod('pathways.api.application.withdraw_application', {
      application_name: applicationName,
    })
  },
  deleteApplication(application) {
    return callMethod('pathways.api.application.delete_application', { application })
  },
}

function serverMessages(body) {
  const messages = []
  try {
    for (const m of JSON.parse(body._server_messages || '[]')) messages.push(JSON.parse(m).message)
  } catch {
    // malformed — fall through to the generic message
  }
  if (body.exc_type === 'RateLimitExceededError' || body.exc_type === 'TooManyRequestsError') {
    return ['Too many attempts from your network. Please wait a few minutes and try again.']
  }
  return messages.length ? messages : ['Something went wrong. Please try again.']
}
