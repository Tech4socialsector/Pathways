import dayjs from 'dayjs'

/**
 * Apply-form checks run in the browser, so candidates see problems under
 * each field before submitting. Mirrors validate_submission in
 * pathways/utils/application_form.py — the server is authoritative and
 * returns the same field keys; this is UX only.
 *
 * Returns { [fieldKey]: message } in form order.
 */

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

export function mobileError(value) {
  const number = (value || '').replace(/[\s-]/g, '')
  if (number.startsWith('+')) {
    return /^\+[1-9][0-9]{7,14}$/.test(number) ? '' : 'Enter a valid mobile number with country code, e.g. +44 7911 123456.'
  }
  return /^[6-9][0-9]{9}$/.test(number) ? '' : 'Enter a valid 10-digit mobile number.'
}

// Mirrors validate_submission: a question with show_if_previous_answer is
// shown (and checked) only when the question above has that answer.
export function isQuestionVisible(q, questions, answers) {
  if (!q.show_if_previous_answer) return true
  const index = questions.findIndex((x) => x.idx === q.idx)
  const previous = questions[index - 1]
  return !!previous && isQuestionVisible(previous, questions, answers) && answers[previous.idx]?.answer === q.show_if_previous_answer
}

const blank = (v) => v === null || v === undefined || String(v).trim() === ''
const isNumber = (v) => !blank(v) && /^\d+(\.\d+)?$/.test(String(v).trim())

export function validateApplication({ data, answers, documents, form, viewer }) {
  const errors = {}
  const add = (key, message) => {
    if (!errors[key]) errors[key] = message
  }
  const required = (key, value, label) => {
    if (blank(value)) add(key, `${label} is required.`)
    return !blank(value)
  }
  const today = dayjs().startOf('day')
  const c = data.candidate
  const app = data.application
  const sec = form.sections || {}
  const opt = form.options || {}
  const wholeNumber = (key, value, label, { min = 0, max = 720, optional = false } = {}) => {
    if (blank(value)) return optional || add(key, `${label} is required.`)
    const n = Number(String(value).trim())
    if (!/^\d+$/.test(String(value).trim()) || n < min || n > max) add(key, `${label}: enter a whole number${max ? ` up to ${max}` : ''}.`)
  }
  const yesNo = (key, value) => {
    if (value !== 'Yes' && value !== 'No') add(key, 'Please answer Yes or No.')
  }

  // --- area of specialization
  if (sec.specialization && !app.specializations?.length && blank(app.other_specialization)) {
    add('academic.specializations', 'Choose at least one area of specialization.')
  }

  // --- personal details
  if (!viewer.logged_in && required('candidate.email', c.email, 'Email') && !EMAIL_RE.test(c.email.trim())) {
    add('candidate.email', 'Enter a valid email address.')
  }
  if (required('candidate.full_name', c.full_name, 'Name') && !/\p{L}/u.test(c.full_name)) {
    add('candidate.full_name', 'Enter your name.')
  }
  if (required('candidate.mobile_number', c.mobile_number, 'Mobile Number') && mobileError(c.mobile_number)) {
    add('candidate.mobile_number', mobileError(c.mobile_number))
  }
  const dob = c.date_of_birth ? dayjs(c.date_of_birth) : null
  if (required('candidate.date_of_birth', c.date_of_birth, 'Date of Birth')) {
    if (!dob.isValid() || !dob.isBefore(today) || today.diff(dob, 'year') > 100) {
      add('candidate.date_of_birth', 'Enter a valid Date of Birth.')
    } else if (today.diff(dob, 'year') < 18) {
      add('candidate.date_of_birth', 'You must be at least 18 years old to apply.')
    }
  }
  required('candidate.gender', c.gender, 'Gender')
  required('candidate.address', c.address, 'Address for Correspondence')
  if (sec.category_disability) {
    required('candidate.category', c.category, 'Category')
    if (app.disability_type) {
      wholeNumber('application.disability_percentage', app.disability_percentage, 'Percentage of disability', { min: 1, max: 100 })
    }
  }

  // --- qualifications
  for (const q of app.qualifications) {
    if (q.degree_level === 'Doctoral') continue
    const isUG = q.degree_level === 'Undergraduate'
    const label = isUG ? 'Graduate Degree' : 'Post Graduate Degree'
    const mandatory = isUG || !!form.require_postgraduate
    const filled = ['degree_name', 'other_institution', 'year_of_graduation'].some((k) => !blank(q[k]))
    if (!filled && !mandatory) continue
    const k = (f) => `qual.${q.degree_level}.${f}`
    required(k('degree_name'), q.degree_name, 'Name of the Degree')
    required(k('other_institution'), q.other_institution, 'College / University')
    if (required(k('year_of_graduation'), q.year_of_graduation, 'Year of Graduation')) {
      const year = Number(q.year_of_graduation)
      if (!/^\d{4}$/.test(String(q.year_of_graduation).trim()) || year < 1950 || year > today.year() + 1) {
        add(k('year_of_graduation'), 'Enter a valid year (YYYY).')
      } else if (dob?.isValid() && year < dob.year() + 15) {
        add(k('year_of_graduation'), 'Year of graduation does not match your Date of Birth.')
      }
    }
    if (required(k('percentage_or_cgpa'), q.percentage_or_cgpa, 'Percentage')) {
      const pct = String(q.percentage_or_cgpa).trim().replace(/%$/, '')
      if (!isNumber(pct)) add(k('percentage_or_cgpa'), 'Enter the percentage as a number (convert CGPA first).')
      else if (Number(pct) > 100) add(k('percentage_or_cgpa'), 'Percentage must be between 0 and 100.')
    }
    if (!blank(q.cgpa) || !blank(q.cgpa_scale)) {
      if (!isNumber(q.cgpa) || !isNumber(q.cgpa_scale)) add(k('cgpa'), 'Enter the CGPA and its scale as numbers, e.g. 7.5 and 10.')
      else if (Number(q.cgpa) > Number(q.cgpa_scale) || Number(q.cgpa_scale) <= 0) add(k('cgpa'), 'The CGPA must be between 0 and the scale.')
    }
    required(k('division_grade'), q.division_grade, 'Division / Grade')
    required(k('specialization'), q.specialization, 'Specialization')
    required(k('transcript_attachment'), q.transcript_attachment, 'Transcript')
    required(k('certificate_attachment'), q.certificate_attachment, 'Degree Certificate')
  }

  // --- PhD
  if (sec.phd) {
    yesNo('application.phd_awarded', app.phd_awarded)
    const d = app.qualifications.find((q) => q.degree_level === 'Doctoral') || {}
    if (app.phd_awarded === 'Yes') {
      required('qual.Doctoral.degree_name', d.degree_name, 'Name of the Doctoral Degree')
      required('qual.Doctoral.other_institution', d.other_institution, 'University')
      if (required('qual.Doctoral.year_of_graduation', d.year_of_graduation, 'Year of Award')) {
        const year = Number(d.year_of_graduation)
        if (!/^\d{4}$/.test(String(d.year_of_graduation).trim()) || year < 1950 || year > today.year()) {
          add('qual.Doctoral.year_of_graduation', 'Enter a valid year (YYYY).')
        }
      }
      required('qual.Doctoral.specialization', d.specialization, 'Specialization')
      for (const rank of ['qs_rank', 'the_rank', 'arwu_rank']) {
        wholeNumber(`qual.Doctoral.${rank}`, d[rank], 'Ranking', { min: 1, max: 100000, optional: true })
      }
    }
  }

  // --- NET / SLET / SET
  if (sec.net) {
    yesNo('application.net_qualified', app.net_qualified)
    if (app.net_qualified === 'Yes') {
      required('application.net_exam', app.net_exam, 'Exam qualified')
      if (blank(app.net_subject) && blank(app.net_other_subject)) add('application.net_subject', 'Subject is required (or enter it under Other).')
      if (required('application.net_award_date', app.net_award_date, 'Date of Award') && dayjs(app.net_award_date).isAfter(today)) {
        add('application.net_award_date', 'Date of Award cannot be in the future.')
      }
      required('application.net_roll_number', app.net_roll_number, 'Roll Number')
    }
  }

  // --- experience
  if (sec.experience_months) {
    wholeNumber('application.overall_experience_months', app.overall_experience_months, 'Overall work experience')
    wholeNumber('application.teaching_experience_months', app.teaching_experience_months, 'Teaching experience')
    wholeNumber('application.research_experience_months', app.research_experience_months, 'Research experience', { optional: true })
    wholeNumber('application.legal_experience_months', app.legal_experience_months, 'Professional legal experience', { optional: true })
    if (Number(app.teaching_experience_months) > Number(app.overall_experience_months)) {
      add('application.teaching_experience_months', 'Teaching experience cannot exceed overall experience.')
    }
  } else {
    const years = (key, value, label) => {
      if (blank(value)) return add(key, `${label} is required (enter 0 if none).`)
      if (!isNumber(value) || Number(value) > 60) return add(key, `${label}: enter years as a number, e.g. 4 or 4.5.`)
    }
    years('application.overall_experience_years', app.overall_experience_years, 'Overall work experience')
    years('application.relevant_experience_years', app.relevant_experience_years, 'Relevant work experience')
    if (isNumber(app.overall_experience_years) && isNumber(app.relevant_experience_years)) {
      if (Number(app.relevant_experience_years) > Number(app.overall_experience_years)) {
        add('application.relevant_experience_years', 'Relevant experience cannot exceed overall experience.')
      }
    }
  }
  const overallYears = sec.experience_months ? Number(app.overall_experience_months) / 12 : Number(app.overall_experience_years)

  let employmentRows = 0
  app.employment_history.forEach((e, idx) => {
    if (!['designation', 'employer_name', 'from_date'].some((f) => !blank(e[f]))) return
    employmentRows++
    const k = (f) => `emp.${idx}.${f}`
    required(k('designation'), e.designation, 'Designation')
    required(k('employer_name'), e.employer_name, 'Name of the employer')
    const from = e.from_date ? dayjs(e.from_date) : null
    if (required(k('from_date'), e.from_date, 'From Date') && from.isAfter(today)) {
      add(k('from_date'), 'From Date cannot be in the future.')
    }
    if (!e.is_current) {
      const to = e.to_date ? dayjs(e.to_date) : null
      if (!to) add(k('to_date'), "To Date is required (or tick 'I currently work here').")
      else if (from && to.isBefore(from)) add(k('to_date'), 'To Date cannot be before From Date.')
      else if (to.isAfter(today)) add(k('to_date'), 'To Date cannot be in the future.')
    }
    if (idx === 0) required(k('key_responsibilities'), e.key_responsibilities, 'Key Responsibilities')
  })
  if (overallYears > 0 && !employmentRows) {
    add('emp.0.designation', 'Add at least your most recent organisation.')
  }
  if (employmentRows) required('application.notice_period', app.notice_period, 'Current Notice Period')

  // --- administrative responsibilities
  if (sec.admin_responsibilities) {
    yesNo('application.held_admin_responsibility', app.held_admin_responsibility)
    if (app.held_admin_responsibility === 'Yes') {
      const rows = app.administrative_responsibilities || []
      const filled = rows.filter((r) => ['responsibility_type', 'duration_months', 'details'].some((f) => !blank(r[f])))
      if (!filled.length) add('admin.0.responsibility_type', 'Add at least one administrative responsibility.')
      rows.forEach((r, idx) => {
        if (!filled.includes(r)) return
        required(`admin.${idx}.responsibility_type`, r.responsibility_type, 'Type of responsibility')
        wholeNumber(`admin.${idx}.duration_months`, r.duration_months, 'Duration', { min: 1 })
        required(`admin.${idx}.details`, r.details, 'Details of the position')
      })
    }
  }

  // --- publications
  if (sec.publications) {
    const pubs = app.publications || []
    const isFilled = (p) => ['title', 'journal_name', 'doi_link', 'pdf_attachment'].some((f) => !blank(p[f]))
    pubs.forEach((p, idx) => {
      if (idx >= sec.min_publications && !isFilled(p)) return
      required(`pub.${idx}.title`, p.title, 'Title')
      required(`pub.${idx}.journal_name`, p.journal_name, 'Name of the journal / publisher')
      required(`pub.${idx}.doi_link`, p.doi_link, 'Link / DOI')
      required(`pub.${idx}.pdf_attachment`, p.pdf_attachment, 'PDF')
    })
  }

  // --- screening questions
  for (const q of form.screening_questions) {
    if (!isQuestionVisible(q, form.screening_questions, answers)) continue
    const a = answers[q.idx] || {}
    const key = `screening.${q.idx}`
    if (blank(a.answer)) {
      if (q.mandatory) add(key, 'Please answer this question.')
      continue
    }
    if (q.answer_type === 'Number' && !/^-?\d+(\.\d+)?$/.test(String(a.answer).trim())) add(key, 'Enter a number.')
    if (q.ask_details_if_yes && a.answer === 'Yes' && blank(a.details)) add(`${key}.details`, 'Please add details.')
  }

  // --- references
  const ownEmail = (viewer.logged_in ? viewer.email : c.email || '').trim().toLowerCase()
  app.references.forEach((r, idx) => {
    const k = (f) => `ref.${idx}.${f}`
    required(k('referee_name'), r.referee_name, 'Name')
    required(k('current_designation_org'), r.current_designation_org, 'Current Designation and Organization')
    required(k('relationship'), r.relationship, 'Nature of Relationship')
    if (required(k('email'), r.email, 'Email Address')) {
      const email = r.email.trim().toLowerCase()
      if (!EMAIL_RE.test(email)) add(k('email'), 'Enter a valid email address.')
      else if (email === ownEmail) add(k('email'), 'You cannot give your own email as a referee.')
    }
    if (required(k('mobile'), r.mobile, 'Mobile Number') && mobileError(r.mobile)) add(k('mobile'), mobileError(r.mobile))
  })
  const [r1, r2] = app.references
  if (r1?.email && r2?.email && r1.email.trim().toLowerCase() === r2.email.trim().toLowerCase()) {
    add('ref.1.email', 'The two referees must be different people.')
  }

  // --- documents
  required('application.resume_attachment', app.resume_attachment, 'Resume / CV')
  required('application.sop_attachment', app.sop_attachment, 'Statement of Purpose')
  for (const d of form.required_documents) {
    if (d.mandatory) required(`doc.${d.document_type}`, documents[d.document_type], d.label)
  }

  // --- other details
  for (const [key, label] of [
    ['current_salary', 'Current Salary'],
    ['expected_salary', 'Expected Salary'],
  ]) {
    const value = app[key]
    if (blank(value)) add(`application.${key}`, `${label} is required (enter 0 if not applicable).`)
    else if (!isNumber(value)) add(`application.${key}`, `${label}: enter the amount in digits only, e.g. 45000.`)
  }
  if (required('application.earliest_doj', app.earliest_doj, 'Earliest Date of Joining') && dayjs(app.earliest_doj).isBefore(today)) {
    add('application.earliest_doj', 'Earliest Date of Joining cannot be in the past.')
  }
  if (blank(app.source)) add('application.source', 'Tell us how you heard about this position.')

  if (!data.declaration_accepted) add('declaration', 'You must accept the declaration to submit.')

  return errors
}
