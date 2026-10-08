// Helpers for the in-app Master Setup forms, which render a master from its
// DocType meta (pathways.api.master_setup.get_master_form) the way the desk
// form does: same fields, sections, defaults and depends_on rules.

import { masterSetupService } from '@/services/masterSetup'

export const LAYOUT_TYPES = ['Section Break', 'Column Break', 'Tab Break']
const INT_TYPES = ['Int', 'Check']
const FLOAT_TYPES = ['Float', 'Percent', 'Currency']
export const NUMBER_TYPES = ['Int', 'Float', 'Percent', 'Currency']
export const TEXT_TYPES = ['Small Text', 'Text', 'Long Text']

export const slugOf = (doctype) => doctype.toLowerCase().trim().replace(/\s+/g, '-')

export const listRoute = (doctype) => ({ name: 'MasterList', params: { slug: slugOf(doctype) } })
// New and edit share one route record, so the form page keeps one set of
// navigation guards when "Create" moves it from /new to /edit/<name>.
export const newRoute = (doctype) => ({ name: 'MasterForm', params: { slug: slugOf(doctype), mode: 'new' } })
export const editRoute = (doctype, name) => ({ name: 'MasterForm', params: { slug: slugOf(doctype), mode: 'edit', name } })

// slug -> registry entry. The registry only changes on deploy, so one fetch
// per page load is enough; a failed fetch is retried next time.
let registry = null
export async function resolveMaster(slug) {
  registry ||= masterSetupService.getMasterSetup().catch((e) => {
    registry = null
    throw e
  })
  const categories = (await registry) || []
  return categories.flatMap((c) => c.masters).find((m) => slugOf(m.doctype) === slug) || null
}

export const hasValue = (f) => !LAYOUT_TYPES.includes(f.fieldtype)

// depends_on / mandatory_depends_on / read_only_depends_on, as the desk
// evaluates them: "eval:<js>" against doc (and parent for child rows), or a
// bare fieldname that must be truthy. The expressions come from DocType
// meta, which only administrators can change — the desk runs them the same way.
const compiled = new Map()
export function evaluate(expression, doc, parent, fallback = true) {
  if (!expression) return fallback
  const expr = String(expression).trim()
  if (!expr.startsWith('eval:')) {
    const value = doc?.[expr]
    return Array.isArray(value) ? value.length > 0 : Boolean(value)
  }
  const code = expr.slice(5)
  if (!compiled.has(code)) {
    try {
      // eslint-disable-next-line no-new-func
      compiled.set(code, new Function('doc', 'parent', `return (${code})`))
    } catch {
      compiled.set(code, null)
    }
  }
  const fn = compiled.get(code)
  if (!fn) return fallback
  try {
    return Boolean(fn(doc || {}, parent || doc || {}))
  } catch {
    return fallback
  }
}

export const isVisible = (f, doc, parent) => evaluate(f.depends_on, doc, parent, true)
export const isRequired = (f, doc, parent) => Boolean(f.reqd) || evaluate(f.mandatory_depends_on, doc, parent, false)
export const isReadOnly = (f, doc, parent) => Boolean(f.read_only) || evaluate(f.read_only_depends_on, doc, parent, false)

// Sections -> columns -> fields, mirroring the desk layout.
export function buildSections(fields) {
  const sections = []
  let current = { key: '__first', label: '', depends_on: null, columns: [[]] }
  for (const f of fields) {
    if (f.fieldtype === 'Section Break' || f.fieldtype === 'Tab Break') {
      sections.push(current)
      current = { key: f.fieldname, label: f.label, depends_on: f.depends_on, columns: [[]] }
    } else if (f.fieldtype === 'Column Break') {
      current.columns.push([])
    } else {
      current.columns[current.columns.length - 1].push(f)
    }
  }
  sections.push(current)
  return sections
    .map((s) => ({ ...s, columns: s.columns.filter((c) => c.length) }))
    .filter((s) => s.columns.length)
}

export function defaultValue(f) {
  if (f.fieldtype === 'Table') return []
  const d = f.default
  if (d === null || d === undefined || d === '') return f.fieldtype === 'Check' ? 0 : null
  // Dynamic defaults (Today, __user, :Link) are left to the server.
  if (typeof d === 'string' && (d.startsWith(':') || d.startsWith('__') || ['Today', 'Now'].includes(d))) return null
  if (INT_TYPES.includes(f.fieldtype)) return parseInt(d, 10) || 0
  if (FLOAT_TYPES.includes(f.fieldtype)) return parseFloat(d) || 0
  return d
}

let rowKey = 0
export function newRecord(fields) {
  const doc = {}
  for (const f of fields) if (hasValue(f)) doc[f.fieldname] = defaultValue(f)
  return doc
}
export function newRow(fields, index) {
  const row = { __key: `new-${++rowKey}` }
  for (const f of fields) if (hasValue(f)) row[f.fieldname] = defaultValue(f)
  // Approval steps and similar: number new rows in order.
  const seq = fields.find((f) => f.fieldname === 'sequence' && f.fieldtype === 'Int')
  if (seq && !row.sequence) row.sequence = index + 1
  return row
}

export function isEmpty(f, value) {
  if (value === null || value === undefined) return true
  if (f.fieldtype === 'Table') return !value.length
  if (f.fieldtype === 'Check') return false
  if (NUMBER_TYPES.includes(f.fieldtype)) return value === ''
  if (f.fieldtype === 'Text Editor') return !String(value).replace(/<[^>]*>|&nbsp;/g, '').trim()
  return !String(value).trim()
}

/** Required-field check on what is shown. Returns { path: message }, where
 * path is "fieldname" or "table.rowIndex.fieldname". The server re-checks
 * everything on save; this only gives instant, per-field feedback. */
export function validateRecord(form, doc, sections) {
  const errors = {}
  const visibleSections = sections.filter((s) => isVisible(s, doc))
  for (const section of visibleSections) {
    for (const f of section.columns.flat()) {
      if (!isVisible(f, doc)) continue
      if (isRequired(f, doc) && isEmpty(f, doc[f.fieldname])) {
        errors[f.fieldname] = f.fieldtype === 'Table' ? `Add at least one row to ${f.label}.` : `${f.label} is required.`
      }
      if (f.fieldtype !== 'Table') continue
      const childFields = form.child_tables[f.options]?.fields || []
      ;(doc[f.fieldname] || []).forEach((row, i) => {
        for (const cf of childFields) {
          if (!hasValue(cf) || !isVisible(cf, row, doc)) continue
          if (isRequired(cf, row, doc) && isEmpty(cf, row[cf.fieldname])) {
            errors[`${f.fieldname}.${i}.${cf.fieldname}`] = `${cf.label} is required.`
          }
        }
      })
    }
  }
  return errors
}

function coerce(f, value) {
  if (f.fieldtype === 'Check') return value ? 1 : 0
  if (NUMBER_TYPES.includes(f.fieldtype)) {
    if (value === '' || value === null || value === undefined) return null
    const n = f.fieldtype === 'Int' ? parseInt(value, 10) : parseFloat(value)
    return Number.isNaN(n) ? null : n
  }
  return value === undefined ? null : value
}

/** The record as the server expects it: typed values, row order in idx, no
 * client-only keys. */
export function toPayload(form, doc) {
  const out = { ...doc }
  for (const f of form.fields) {
    if (!hasValue(f)) continue
    if (f.fieldtype === 'Table') {
      const childFields = (form.child_tables[f.options]?.fields || []).filter(hasValue)
      out[f.fieldname] = (doc[f.fieldname] || []).map((row, i) => {
        const r = {}
        for (const [k, v] of Object.entries(row)) if (!k.startsWith('__')) r[k] = v
        for (const cf of childFields) r[cf.fieldname] = coerce(cf, row[cf.fieldname])
        r.idx = i + 1
        return r
      })
    } else {
      out[f.fieldname] = coerce(f, doc[f.fieldname])
    }
  }
  for (const k of Object.keys(out)) if (k.startsWith('__')) delete out[k]
  return out
}

/** Table rows from the server get a stable client key for v-for. */
export function withRowKeys(form, doc) {
  for (const f of form.fields) {
    if (f.fieldtype === 'Table') {
      doc[f.fieldname] = (doc[f.fieldname] || []).map((row) => ({ ...row, __key: row.name || `new-${++rowKey}` }))
    }
  }
  return doc
}

/** First error message from a failed frappe-ui call. */
export function errorText(e, fallback = 'Something went wrong. Please try again.') {
  const messages = e?.messages?.filter(Boolean)
  if (messages?.length) return messages.map((m) => String(m).replace(/<[^>]*>/g, '')).join(' ')
  return fallback
}

// Link searches, shared by every Link field: a table of ten Document Type
// rows makes one request, not ten. Cleared whenever a master is saved or
// deleted, so a record just created is offered straight away.
const LINK_CACHE_MS = 30000
const linkCache = new Map()
export function searchLink(doctype, txt) {
  const key = `${doctype}\u0000${txt}`
  const hit = linkCache.get(key)
  if (hit && Date.now() - hit.at < LINK_CACHE_MS) return hit.promise
  const promise = masterSetupService.searchLink(doctype, txt).catch((e) => {
    linkCache.delete(key)
    throw e
  })
  linkCache.set(key, { at: Date.now(), promise })
  return promise
}
export function clearLinkCache() {
  linkCache.clear()
}
