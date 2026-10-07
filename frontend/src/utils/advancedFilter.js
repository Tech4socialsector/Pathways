// Conditions for the list Filter builder (AdvancedFilter.vue), and the
// matching DataTable applies to each row.
import dayjs from 'dayjs'

export const NO_VALUE = new Set(['set', 'not_set'])

const OPS = {
  text: [
    { value: 'like', label: 'Contains' },
    { value: 'eq', label: 'Equals' },
    { value: 'neq', label: 'Not equals' },
    { value: 'not_like', label: 'Does not contain' },
    { value: 'set', label: 'Is set' },
    { value: 'not_set', label: 'Is not set' },
  ],
  number: [
    { value: 'eq', label: '=' },
    { value: 'neq', label: '≠' },
    { value: 'gt', label: '>' },
    { value: 'gte', label: '≥' },
    { value: 'lt', label: '<' },
    { value: 'lte', label: '≤' },
    { value: 'between', label: 'Between' },
    { value: 'set', label: 'Is set' },
    { value: 'not_set', label: 'Is not set' },
  ],
  date: [
    { value: 'eq', label: 'On' },
    { value: 'lt', label: 'Before' },
    { value: 'gt', label: 'After' },
    { value: 'between', label: 'Between' },
    { value: 'set', label: 'Is set' },
    { value: 'not_set', label: 'Is not set' },
  ],
}

export function conditionOps(type) {
  return OPS[type] || OPS.text
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}/

/** 'number' | 'date' | 'text', from the column's `type` or its values. */
export function valueType(col, rows) {
  if (!col) return 'text'
  if (col.type) return col.type
  let seen = 0
  let numbers = 0
  let dates = 0
  for (const row of rows) {
    const v = row[col.key]
    if (v === null || v === undefined || v === '') continue
    seen++
    if (typeof v === 'number' || (typeof v === 'string' && v.trim() !== '' && !isNaN(Number(v)) && !DATE_RE.test(v))) numbers++
    else if (typeof v === 'string' && DATE_RE.test(v)) dates++
    if (seen >= 50) break
  }
  if (!seen) return 'text'
  if (numbers === seen) return 'number'
  if (dates === seen) return 'date'
  return 'text'
}

const empty = (v) => v === null || v === undefined || v === ''

/** Does `row` meet every condition? `display(row, col)` gives the shown text. */
export function matchesConditions(row, conditions, columns, rows, display) {
  for (const c of conditions) {
    const col = columns.find((x) => x.key === c.key)
    if (!col) continue
    const raw = row[c.key]
    if (c.op === 'set') {
      if (empty(raw)) return false
      continue
    }
    if (c.op === 'not_set') {
      if (!empty(raw)) return false
      continue
    }
    const type = valueType(col, rows)
    if (type === 'number') {
      if (empty(raw)) return false
      const n = Number(raw)
      const a = Number(c.value)
      const b = Number(c.value2)
      const ok = {
        eq: n === a, neq: n !== a, gt: n > a, gte: n >= a, lt: n < a, lte: n <= a,
        between: n >= Math.min(a, b) && n <= Math.max(a, b),
      }[c.op]
      if (!ok) return false
    } else if (type === 'date') {
      if (empty(raw)) return false
      const d = dayjs(raw).format('YYYY-MM-DD')
      const a = c.value
      const b = c.value2 || c.value
      const ok = {
        eq: d === a, lt: d < a, gt: d > a,
        between: d >= (a < b ? a : b) && d <= (a < b ? b : a),
      }[c.op]
      if (!ok) return false
    } else {
      const shown = String(display(row, col) ?? '').toLowerCase()
      const rawText = String(raw ?? '').toLowerCase()
      const v = String(c.value).trim().toLowerCase()
      const equal = shown === v || rawText === v
      const ok = {
        eq: equal,
        neq: !equal,
        like: shown.includes(v) || rawText.includes(v),
        not_like: !shown.includes(v) && !rawText.includes(v),
      }[c.op]
      if (!ok) return false
    }
  }
  return true
}
