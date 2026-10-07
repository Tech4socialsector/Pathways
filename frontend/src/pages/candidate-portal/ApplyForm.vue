<template>
  <CandidatePortalLayout>
    <div class="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <div v-if="jobLoading && !job" class="text-sm text-gray-500">Loading...</div>
      <EmptyState
        v-else-if="!job"
        title="This position is not open"
        description="It may have closed or the link may be wrong."
      >
        <template #action><Button @click="$router.push('/portal/jobs')">See current openings</Button></template>
      </EmptyState>

      <template v-else>
        <BackButton :fallback="`/portal/jobs/${props.id}`" class="mb-4" />
        <header class="overflow-hidden rounded-xl border bg-white shadow-sm">
          <div class="border-b bg-gradient-to-r from-brand-50 to-white px-5 py-5 sm:px-6">
            <div class="text-xs font-bold uppercase tracking-wider text-brand-700">Application Form</div>
            <h1 class="mt-1 text-2xl font-bold text-gray-900">{{ job.job_title }}</h1>
            <div class="mt-3 flex flex-wrap gap-2 text-xs text-gray-700">
              <span v-for="chip in jobChips" :key="chip.text" class="inline-flex items-center gap-1.5 rounded-full border bg-white px-2.5 py-1">
                <FeatherIcon :name="chip.icon" class="h-3.5 w-3.5 text-gray-400" />{{ chip.text }}
              </span>
            </div>
            <p
              v-if="form.application_deadline"
              class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium"
              :class="form.is_open ? 'text-amber-700' : 'text-red-600'"
            >
              <FeatherIcon name="clock" class="h-4 w-4" />
              Applications close {{ formatDateTime(form.application_deadline) }} (IST)
            </p>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-3 border-b bg-brand-700 px-5 py-3 text-white sm:px-6">
            <div class="flex items-center gap-2.5 text-sm">
              <FeatherIcon name="info" class="h-5 w-5 shrink-0" />
              <span><strong>Important instructions</strong><span class="hidden sm:inline"> — please read these before you begin.</span></span>
            </div>
            <button
              type="button"
              class="inline-flex items-center gap-1.5 rounded-md bg-white px-3 py-1.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
              @click="showInstructions = true"
            >
              <FeatherIcon name="book-open" class="h-4 w-4" /> View instructions
            </button>
          </div>
          <details v-if="job.jd_text || job.jd_attachment" class="group px-5 py-3 sm:px-6">
            <summary class="flex cursor-pointer list-none items-center justify-between text-sm font-bold text-gray-900">
              Job Description
              <FeatherIcon name="chevron-down" class="h-4 w-4 text-gray-500 transition group-open:rotate-180" />
            </summary>
            <div v-if="job.jd_text" class="prose prose-sm mt-3 max-w-none" v-html="job.jd_text" />
            <a
              v-if="job.jd_attachment"
              :href="job.jd_attachment"
              target="_blank"
              class="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-brand-700 hover:underline"
            >
              <FeatherIcon name="download" class="h-4 w-4" /> Download the full notification
            </a>
          </details>
        </header>

        <!-- Gates -->
        <div v-if="!form.is_open" class="mt-6 rounded-lg border bg-white p-6 text-center text-sm text-gray-700">
          Applications for this position are closed.
        </div>

        <div v-else-if="submitted" class="mt-6 overflow-hidden rounded-xl border bg-white shadow-sm">
          <div class="flex flex-col items-center bg-green-50 px-6 pb-8 pt-10 text-center">
            <div class="flex h-16 w-16 items-center justify-center rounded-full bg-green-500 shadow-[0_0_0_8px_rgb(34_197_94_/_0.15)]">
              <FeatherIcon name="check" class="h-9 w-9 text-white" :stroke-width="3" />
            </div>
            <h2 class="mt-5 text-xl font-semibold text-gray-900">Application submitted successfully</h2>
            <p class="mt-1 text-sm text-gray-600">Thank you for applying to National Law School of India University.</p>

            <div class="mt-6 flex items-center gap-2 rounded-lg border border-green-200 bg-white px-4 py-2.5">
              <div class="text-left">
                <div class="text-xs uppercase tracking-wide text-gray-500">Application ID</div>
                <div class="font-mono text-lg font-semibold text-gray-900">{{ applicationId }}</div>
              </div>
              <Button variant="ghost" :icon="copied ? 'check' : 'copy'" :aria-label="copied ? 'Copied' : 'Copy application ID'" @click="copyApplicationId" />
            </div>
          </div>

          <div class="grid gap-6 px-6 py-6 sm:grid-cols-2">
            <dl class="flex flex-col gap-3 text-sm">
              <div class="flex gap-3">
                <FeatherIcon name="briefcase" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                <div>
                  <dt class="text-gray-500">Position</dt>
                  <dd class="font-medium text-gray-900">{{ job.job_title }}</dd>
                  <dd class="text-gray-600">{{ job.department }}</dd>
                </div>
              </div>
              <div class="flex gap-3">
                <FeatherIcon name="calendar" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                <div>
                  <dt class="text-gray-500">Submitted on</dt>
                  <dd class="font-medium text-gray-900">{{ submittedAt }}</dd>
                </div>
              </div>
              <div class="flex gap-3">
                <FeatherIcon name="mail" class="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                <div>
                  <dt class="text-gray-500">Confirmation sent to</dt>
                  <dd class="break-all font-medium text-gray-900">{{ submittedEmail }}</dd>
                </div>
              </div>
            </dl>

            <div>
              <div class="mb-3 text-sm font-semibold text-gray-900">What happens next</div>
              <ol class="flex flex-col gap-3 text-sm">
                <li v-for="(step, i) in NEXT_STEPS" :key="step.title" class="flex gap-3">
                  <span
                    class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold"
                    :class="i === 0 ? 'bg-green-500 text-white' : 'bg-gray-100 text-gray-600'"
                  >
                    <FeatherIcon v-if="i === 0" name="check" class="h-3.5 w-3.5" />
                    <template v-else>{{ i + 1 }}</template>
                  </span>
                  <div>
                    <div class="font-medium text-gray-900">{{ step.title }}</div>
                    <div class="text-gray-500">{{ step.text }}</div>
                  </div>
                </li>
              </ol>
            </div>
          </div>

          <div class="flex flex-wrap items-center justify-between gap-3 border-t bg-gray-50 px-6 py-4">
            <p class="text-xs text-gray-500">Please keep your application ID for any communication with us.</p>
            <div class="flex gap-2">
              <Button @click="$router.push('/portal/jobs')">View other openings</Button>
              <Button v-if="viewer.logged_in" variant="solid" @click="$router.push('/portal/applications')">
                Track my applications
              </Button>
            </div>
          </div>
        </div>

        <div v-else-if="viewer.is_staff" class="mt-6 rounded-lg border bg-white p-6 text-sm text-gray-700">
          You are logged in with a staff account ({{ viewer.email }}). To apply, log out and register with your personal
          email address.
        </div>

        <div v-else-if="viewer.already_applied" class="mt-6 rounded-lg border bg-white p-6 text-center text-sm text-gray-700">
          You have already applied for this position (application
          <span class="font-mono">{{ viewer.already_applied }}</span>). An application can be submitted only once.
          <div class="mt-4"><Button @click="$router.push('/portal/applications')">Track my applications</Button></div>
        </div>

        <!-- The form -->
        <form v-else class="mt-6 flex flex-col gap-6 [counter-reset:section]" novalidate @submit.prevent="handleSubmit">
          <p class="text-sm text-gray-600">
            Fields marked <span class="text-red-500">*</span> are required. Your progress is saved on this device until you
            submit.
          </p>

          <Section v-if="sec.specialization" title="Area of Specialization" subtitle="Must be relevant to the area notified in the advertisement. Choose all that apply.">
            <FormField name="academic.specializations" :error="errors['academic.specializations']">
              <div class="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2 lg:grid-cols-3">
                <label v-for="name in opt.specializations || []" :key="name" class="flex items-center gap-2 text-sm text-gray-700">
                  <input v-model="data.application.specializations" type="checkbox" :value="name" class="rounded border-gray-300" />
                  {{ name }}
                </label>
              </div>
              <FormControl
                class="mt-4 sm:w-1/2"
                label="Other specialization (if not listed)"
                v-model="data.application.other_specialization"
              />
            </FormField>
          </Section>

          <Section title="Personal Details">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField name="candidate.email" :error="errors['candidate.email']">
                <FormControl v-if="viewer.logged_in" label="Email" :model-value="viewer.email" disabled />
                <FormControl v-else label="Email" type="email" v-model="data.candidate.email" placeholder="you@example.com" required />
              </FormField>
              <FormField name="candidate.full_name" :error="errors['candidate.full_name']">
                <FormControl label="Name" v-model="data.candidate.full_name" required />
              </FormField>
              <FormField name="candidate.mobile_number" :error="errors['candidate.mobile_number']">
                <FormControl
                  label="Mobile Number"
                  type="tel"
                  v-model="data.candidate.mobile_number"
                  placeholder="10-digit number, or +country code"
                  required
                />
              </FormField>
              <FormField name="candidate.date_of_birth" :error="errors['candidate.date_of_birth']">
                <div class="grid grid-cols-[1fr_auto] items-end gap-3">
                  <FormControl label="Date of Birth" type="date" v-model="data.candidate.date_of_birth" :max="today" required />
                  <div class="pb-2 text-sm text-gray-600">{{ age !== null ? `Age ${age}` : '' }}</div>
                </div>
              </FormField>
              <FormField name="candidate.gender" :error="errors['candidate.gender']">
                <FormControl
                  label="Gender"
                  type="select"
                  v-model="data.candidate.gender"
                  :options="['', 'Female', 'Male', 'Prefer not to say', 'Other']"
                  required
                />
              </FormField>
              <template v-if="sec.category_disability">
                <FormField name="candidate.category" :error="errors['candidate.category']">
                  <FormControl label="Category" type="select" v-model="data.candidate.category" :options="['', ...(opt.categories || [])]" required />
                </FormField>
                <FormField name="application.disability_type" :error="errors['application.disability_type']">
                  <FormControl
                    label="Type of Disability (if any)"
                    type="select"
                    v-model="data.application.disability_type"
                    :options="['', ...(opt.disability_types || [])]"
                  />
                </FormField>
                <FormField
                  v-if="data.application.disability_type"
                  name="application.disability_percentage"
                  :error="errors['application.disability_percentage']"
                >
                  <FormControl label="Percentage of Disability" inputmode="numeric" v-model="data.application.disability_percentage" required />
                </FormField>
              </template>
            </div>
            <FormField class="mt-4" name="candidate.address" :error="errors['candidate.address']">
              <FormControl label="Address for Correspondence" type="textarea" v-model="data.candidate.address" required />
            </FormField>
          </Section>

          <Section
            v-for="q in data.application.qualifications.filter((x) => x.degree_level !== 'Doctoral')"
            :key="q.degree_level"
            :title="q.degree_level === 'Undergraduate' ? 'Graduate Degree' : 'Post Graduate Degree'"
            :badge="q.degree_level === 'Postgraduate' && !form.require_postgraduate ? 'optional' : ''"
          >
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField :name="`qual.${q.degree_level}.degree_name`" :error="errors[`qual.${q.degree_level}.degree_name`]">
                <FormControl label="Name of the Degree" v-model="q.degree_name" :required="isRequiredDegree(q)" />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.other_institution`" :error="errors[`qual.${q.degree_level}.other_institution`]">
                <template v-if="opt.institutions">
                  <span class="mb-1.5 block text-sm text-gray-700">
                    College / University<span v-if="isRequiredDegree(q)" class="text-red-500"> *</span>
                  </span>
                  <Autocomplete
                    placeholder="Search your university"
                    :options="institutionOptions"
                    :model-value="q._other ? OTHER : q.other_institution"
                    @update:model-value="(o) => pickInstitution(q, o?.value)"
                  />
                  <FormControl v-if="q._other" class="mt-2" placeholder="Name of your College / University" v-model="q.other_institution" />
                </template>
                <FormControl v-else label="College / University" v-model="q.other_institution" :required="isRequiredDegree(q)" />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.year_of_graduation`" :error="errors[`qual.${q.degree_level}.year_of_graduation`]">
                <FormControl
                  label="Year of Graduation"
                  inputmode="numeric"
                  maxlength="4"
                  placeholder="YYYY"
                  v-model="q.year_of_graduation"
                  :required="isRequiredDegree(q)"
                />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.percentage_or_cgpa`" :error="errors[`qual.${q.degree_level}.percentage_or_cgpa`]">
                <FormControl
                  label="Percentage"
                  inputmode="decimal"
                  v-model="q.percentage_or_cgpa"
                  :required="isRequiredDegree(q)"
                  description="Exact percentage. If you have a CGPA, convert it using your university's table."
                />
              </FormField>
              <FormField v-if="academicForm" :name="`qual.${q.degree_level}.cgpa`" :error="errors[`qual.${q.degree_level}.cgpa`]">
                <div class="grid grid-cols-2 gap-3">
                  <FormControl label="CGPA (if applicable)" inputmode="decimal" v-model="q.cgpa" placeholder="e.g. 7.5" />
                  <FormControl label="CGPA scale" inputmode="decimal" v-model="q.cgpa_scale" placeholder="e.g. 10" />
                </div>
              </FormField>
              <FormField :name="`qual.${q.degree_level}.division_grade`" :error="errors[`qual.${q.degree_level}.division_grade`]">
                <FormControl label="Division / Grade" v-model="q.division_grade" :required="isRequiredDegree(q)" />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.specialization`" :error="errors[`qual.${q.degree_level}.specialization`]">
                <FormControl label="Specialization" v-model="q.specialization" :required="isRequiredDegree(q)" />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.transcript_attachment`" :error="errors[`qual.${q.degree_level}.transcript_attachment`]">
                <UploadField
                  v-model="q.transcript_attachment"
                  label="Transcript (with percentage clearly mentioned)"
                  :required="isRequiredDegree(q)"
                  :rule="form.upload_rule"
                />
              </FormField>
              <FormField :name="`qual.${q.degree_level}.certificate_attachment`" :error="errors[`qual.${q.degree_level}.certificate_attachment`]">
                <UploadField v-model="q.certificate_attachment" label="Degree Certificate" :required="isRequiredDegree(q)" :rule="form.upload_rule" />
              </FormField>
            </div>
          </Section>

          <Section v-if="sec.phd" title="Doctoral Degree">
            <FormField name="application.phd_awarded" :error="errors['application.phd_awarded']">
              <YesNo v-model="data.application.phd_awarded" label="Have you been awarded your PhD degree?" />
            </FormField>
            <div v-if="data.application.phd_awarded === 'Yes'" class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField name="qual.Doctoral.degree_name" :error="errors['qual.Doctoral.degree_name']">
                <FormControl label="Name of the Doctoral Degree" v-model="doctoral.degree_name" placeholder="e.g. PhD in Law" required />
              </FormField>
              <FormField name="qual.Doctoral.other_institution" :error="errors['qual.Doctoral.other_institution']">
                <FormControl label="University" v-model="doctoral.other_institution" required />
              </FormField>
              <FormField name="qual.Doctoral.year_of_graduation" :error="errors['qual.Doctoral.year_of_graduation']">
                <FormControl label="Year of Award" inputmode="numeric" maxlength="4" placeholder="YYYY" v-model="doctoral.year_of_graduation" required />
              </FormField>
              <FormField name="qual.Doctoral.specialization" :error="errors['qual.Doctoral.specialization']">
                <FormControl label="Specialization" v-model="doctoral.specialization" required />
              </FormField>
              <div class="sm:col-span-2">
                <div class="mb-2 text-sm text-gray-700">If your PhD is from a foreign university, its world ranking:</div>
                <div class="grid grid-cols-3 gap-3">
                  <FormField v-for="r in RANKS" :key="r.field" :name="`qual.Doctoral.${r.field}`" :error="errors[`qual.Doctoral.${r.field}`]">
                    <FormControl :label="r.label" inputmode="numeric" v-model="doctoral[r.field]" placeholder="e.g. 500" />
                  </FormField>
                </div>
              </div>
              <FormField name="qual.Doctoral.certificate_attachment" :error="errors['qual.Doctoral.certificate_attachment']">
                <UploadField v-model="doctoral.certificate_attachment" label="PhD Certificate" :rule="form.upload_rule" />
              </FormField>
            </div>
          </Section>

          <Section v-if="sec.net" title="NET / SLET / SET">
            <FormField name="application.net_qualified" :error="errors['application.net_qualified']">
              <YesNo v-model="data.application.net_qualified" label="Have you successfully cleared the NET / SLET / SET?" />
            </FormField>
            <div v-if="data.application.net_qualified === 'Yes'" class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField name="application.net_exam" :error="errors['application.net_exam']">
                <FormControl label="Exam qualified" type="select" v-model="data.application.net_exam" :options="['', ...(opt.net_exams || [])]" required />
              </FormField>
              <FormField name="application.net_subject" :error="errors['application.net_subject']">
                <span class="mb-1.5 block text-sm text-gray-700">Subject<span class="text-red-500"> *</span></span>
                <Autocomplete
                  placeholder="Search subject"
                  :options="netSubjectOptions"
                  :model-value="data.application.net_subject"
                  @update:model-value="(o) => (data.application.net_subject = o?.value || '')"
                />
                <FormControl
                  class="mt-2"
                  placeholder="Other subject (if not listed)"
                  v-model="data.application.net_other_subject"
                />
              </FormField>
              <FormField name="application.net_award_date" :error="errors['application.net_award_date']">
                <FormControl label="Date of Award" type="date" :max="today" v-model="data.application.net_award_date" required />
              </FormField>
              <FormField name="application.net_roll_number" :error="errors['application.net_roll_number']">
                <FormControl label="Roll Number" v-model="data.application.net_roll_number" required />
              </FormField>
            </div>
          </Section>

          <Section title="Professional Experience" subtitle="In reverse chronological order — most recent first.">
            <div v-if="sec.experience_months" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField v-for="m in MONTH_FIELDS" :key="m.field" :name="`application.${m.field}`" :error="errors[`application.${m.field}`]">
                <FormControl
                  :label="m.label"
                  inputmode="numeric"
                  v-model="data.application[m.field]"
                  :required="m.required"
                  :description="m.hint"
                />
              </FormField>
              <FormField class="sm:col-span-2" name="application.legal_experience_details" :error="errors['application.legal_experience_details']">
                <FormControl label="Nature of professional legal experience" type="textarea" v-model="data.application.legal_experience_details" />
              </FormField>
            </div>
            <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField name="application.overall_experience_years" :error="errors['application.overall_experience_years']">
                <FormControl label="Overall work experience (years)" inputmode="decimal" v-model="data.application.overall_experience_years" required />
              </FormField>
              <FormField name="application.relevant_experience_years" :error="errors['application.relevant_experience_years']">
                <FormControl label="Relevant work experience (years)" inputmode="decimal" v-model="data.application.relevant_experience_years" required />
              </FormField>
            </div>
            <div v-for="(e, idx) in data.application.employment_history" :key="idx" class="mt-4 rounded border p-3">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium text-gray-900">Organisation #{{ idx + 1 }}</span>
                <Button v-if="idx > 0" size="sm" variant="ghost" @click="data.application.employment_history.splice(idx, 1)">Remove</Button>
              </div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <FormField :name="`emp.${idx}.designation`" :error="errors[`emp.${idx}.designation`]">
                  <FormControl label="Designation" v-model="e.designation" :required="idx === 0" />
                </FormField>
                <FormField :name="`emp.${idx}.employer_name`" :error="errors[`emp.${idx}.employer_name`]">
                  <FormControl label="Name of the employer" v-model="e.employer_name" :required="idx === 0" />
                </FormField>
                <FormField :name="`emp.${idx}.from_date`" :error="errors[`emp.${idx}.from_date`]">
                  <FormControl label="From Date" type="date" v-model="e.from_date" :max="today" :required="idx === 0" />
                </FormField>
                <FormField :name="`emp.${idx}.to_date`" :error="errors[`emp.${idx}.to_date`]">
                  <FormControl v-if="!e.is_current" label="To Date" type="date" v-model="e.to_date" :max="today" :required="idx === 0" />
                  <label class="mt-2 flex items-center gap-2 text-sm text-gray-700">
                    <input v-model="e.is_current" type="checkbox" class="rounded border-gray-300" /> I currently work here
                  </label>
                </FormField>
                <FormField class="sm:col-span-2" :name="`emp.${idx}.key_responsibilities`" :error="errors[`emp.${idx}.key_responsibilities`]">
                  <FormControl label="Key Responsibilities" type="textarea" v-model="e.key_responsibilities" :required="idx === 0" />
                </FormField>
              </div>
            </div>
            <Button class="mt-3" size="sm" variant="ghost" @click="addEmployment">+ Add another organisation</Button>
            <FormField class="mt-4 sm:w-1/2" name="application.notice_period" :error="errors['application.notice_period']">
              <FormControl label="Current Notice Period" v-model="data.application.notice_period" placeholder="e.g. 60 days" />
            </FormField>
          </Section>

          <Section v-if="sec.admin_responsibilities" title="Administrative Responsibilities at a University">
            <FormField name="application.held_admin_responsibility" :error="errors['application.held_admin_responsibility']">
              <YesNo
                v-model="data.application.held_admin_responsibility"
                label="In your previous academic positions, did you undertake any administrative responsibilities?"
              />
            </FormField>
            <template v-if="data.application.held_admin_responsibility === 'Yes'">
              <div v-for="(r, idx) in data.application.administrative_responsibilities" :key="idx" class="mt-4 rounded border p-3">
                <div class="mb-3 flex items-center justify-between">
                  <span class="text-sm font-medium text-gray-900">Responsibility #{{ idx + 1 }}</span>
                  <Button v-if="idx > 0" size="sm" variant="ghost" @click="data.application.administrative_responsibilities.splice(idx, 1)">Remove</Button>
                </div>
                <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <FormField :name="`admin.${idx}.responsibility_type`" :error="errors[`admin.${idx}.responsibility_type`]">
                    <FormControl
                      label="Type of responsibility"
                      type="select"
                      v-model="r.responsibility_type"
                      :options="['', ...(opt.admin_responsibility_types || [])]"
                      required
                    />
                  </FormField>
                  <FormField :name="`admin.${idx}.duration_months`" :error="errors[`admin.${idx}.duration_months`]">
                    <FormControl label="Duration (months)" inputmode="numeric" v-model="r.duration_months" required />
                  </FormField>
                  <FormField class="sm:col-span-2" :name="`admin.${idx}.details`" :error="errors[`admin.${idx}.details`]">
                    <FormControl label="Details of the position" type="textarea" v-model="r.details" required />
                  </FormField>
                </div>
              </div>
              <Button
                v-if="data.application.administrative_responsibilities.length < 5"
                class="mt-3"
                size="sm"
                variant="ghost"
                @click="data.application.administrative_responsibilities.push({})"
              >
                + Add another responsibility
              </Button>
            </template>
          </Section>

          <Section
            v-if="sec.publications"
            title="Publications"
            :subtitle="`Your best ${sec.max_publications} publication(s) from peer-reviewed or Scopus-indexed journals, books or chapters.${sec.min_publications ? ` At least ${sec.min_publications} required.` : ''}`"
          >
            <div v-for="(pub, idx) in data.application.publications" :key="idx" class="mb-4 rounded border p-3 last:mb-0">
              <div class="mb-3 flex items-center justify-between">
                <span class="text-sm font-medium text-gray-900">
                  Publication #{{ idx + 1 }}<span v-if="idx < sec.min_publications" class="text-red-500"> *</span>
                </span>
                <Button v-if="idx >= Math.max(sec.min_publications, 1)" size="sm" variant="ghost" @click="data.application.publications.splice(idx, 1)">
                  Remove
                </Button>
              </div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <FormField class="sm:col-span-2" :name="`pub.${idx}.title`" :error="errors[`pub.${idx}.title`]">
                  <FormControl label="Title of the article / book / chapter" v-model="pub.title" :required="idx < sec.min_publications" />
                </FormField>
                <FormField :name="`pub.${idx}.journal_name`" :error="errors[`pub.${idx}.journal_name`]">
                  <FormControl label="Name of the journal / publisher" v-model="pub.journal_name" :required="idx < sec.min_publications" />
                </FormField>
                <FormField :name="`pub.${idx}.volume`" :error="errors[`pub.${idx}.volume`]">
                  <FormControl label="Volume" v-model="pub.volume" />
                </FormField>
                <FormField :name="`pub.${idx}.doi_link`" :error="errors[`pub.${idx}.doi_link`]">
                  <FormControl label="Link of the article / DOI" v-model="pub.doi_link" :required="idx < sec.min_publications" />
                </FormField>
                <FormField :name="`pub.${idx}.pdf_attachment`" :error="errors[`pub.${idx}.pdf_attachment`]">
                  <UploadField v-model="pub.pdf_attachment" label="PDF" :required="idx < sec.min_publications" :rule="form.upload_rule" />
                </FormField>
              </div>
            </div>
            <Button
              v-if="data.application.publications.length < sec.max_publications"
              size="sm"
              variant="ghost"
              @click="data.application.publications.push({})"
            >
              + Add another publication
            </Button>
          </Section>

          <Section v-if="form.screening_questions.length" title="Eligibility">
            <div class="flex flex-col gap-5">
              <!-- answers[] is filled right after the job loads; guard the render in between. -->
              <FormField
                v-for="q in form.screening_questions.filter((x) => answers[x.idx])"
                :key="q.idx"
                :name="`screening.${q.idx}`"
                :error="errors[`screening.${q.idx}`]"
              >
                <div class="mb-1.5 text-sm text-gray-800">
                  {{ q.question }}<span v-if="q.mandatory" class="text-red-500">*</span>
                </div>
                <div v-if="q.answer_type === 'Yes/No' || q.answer_type === 'Single Choice'" class="flex flex-wrap gap-x-5 gap-y-1.5">
                  <label
                    v-for="opt in q.answer_type === 'Yes/No' ? ['Yes', 'No'] : q.options"
                    :key="opt"
                    class="flex items-center gap-2 text-sm text-gray-700"
                  >
                    <input v-model="answers[q.idx].answer" type="radio" :name="`q${q.idx}`" :value="opt" /> {{ opt }}
                  </label>
                </div>
                <FormControl v-else-if="q.answer_type === 'Long Text'" type="textarea" v-model="answers[q.idx].answer" />
                <FormControl v-else :inputmode="q.answer_type === 'Number' ? 'decimal' : 'text'" v-model="answers[q.idx].answer" />
                <FormField
                  v-if="q.ask_details_if_yes && answers[q.idx].answer === 'Yes'"
                  class="mt-2"
                  :name="`screening.${q.idx}.details`"
                  :error="errors[`screening.${q.idx}.details`]"
                >
                  <FormControl type="textarea" :label="q.details_label" v-model="answers[q.idx].details" required />
                </FormField>
              </FormField>
            </div>
          </Section>

          <Section
            title="References"
            subtitle="Your former or current manager / reporting supervisor. References from colleagues, peers or friends will not be considered."
          >
            <div v-for="(r, idx) in data.application.references" :key="idx" class="mb-4 last:mb-0">
              <div class="mb-2 text-sm font-medium text-gray-900">Referee #{{ idx + 1 }}</div>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <FormField :name="`ref.${idx}.referee_name`" :error="errors[`ref.${idx}.referee_name`]">
                  <FormControl label="Name" v-model="r.referee_name" required />
                </FormField>
                <FormField :name="`ref.${idx}.current_designation_org`" :error="errors[`ref.${idx}.current_designation_org`]">
                  <FormControl label="Current Designation and Organization" v-model="r.current_designation_org" required />
                </FormField>
                <FormField :name="`ref.${idx}.relationship`" :error="errors[`ref.${idx}.relationship`]">
                  <FormControl label="Nature of Relationship" v-model="r.relationship" required placeholder="e.g. Reporting manager" />
                </FormField>
                <FormField :name="`ref.${idx}.email`" :error="errors[`ref.${idx}.email`]">
                  <FormControl label="Email Address" type="email" v-model="r.email" required />
                </FormField>
                <FormField :name="`ref.${idx}.mobile`" :error="errors[`ref.${idx}.mobile`]">
                  <FormControl label="Mobile Number" type="tel" v-model="r.mobile" placeholder="10-digit number, or +country code" required />
                </FormField>
              </div>
            </div>
          </Section>

          <Section title="Supporting Documents">
            <div class="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <FormField name="application.resume_attachment" :error="errors['application.resume_attachment']">
                <UploadField v-model="data.application.resume_attachment" label="Resume / CV" required :rule="form.upload_rule" />
              </FormField>
              <FormField name="application.sop_attachment" :error="errors['application.sop_attachment']">
                <UploadField
                  v-model="data.application.sop_attachment"
                  label="Statement of Purpose"
                  required
                  :rule="form.upload_rule"
                  hint="Why you are interested in this role and how your qualifications, experience, skills and aspirations make you suitable (max 500 words)."
                />
              </FormField>
              <FormField
                v-for="d in form.required_documents"
                :key="d.document_type"
                :name="`doc.${d.document_type}`"
                :error="errors[`doc.${d.document_type}`]"
              >
                <UploadField v-model="documents[d.document_type]" :label="d.label" :required="!!d.mandatory" :rule="d" />
              </FormField>
              <FormField name="application.additional_attachment" :error="errors['application.additional_attachment']">
                <UploadField v-model="data.application.additional_attachment" label="Additional Documents" :rule="form.upload_rule" />
              </FormField>
            </div>
          </Section>

          <Section title="Other Details">
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField name="application.current_salary" :error="errors['application.current_salary']">
                <FormControl label="Current Salary (per month, ₹)" inputmode="decimal" v-model="data.application.current_salary" required />
              </FormField>
              <FormField name="application.expected_salary" :error="errors['application.expected_salary']">
                <FormControl label="Expected Salary (per month, ₹)" inputmode="decimal" v-model="data.application.expected_salary" required />
              </FormField>
              <FormField name="application.earliest_doj" :error="errors['application.earliest_doj']">
                <FormControl label="Earliest Date of Joining" type="date" v-model="data.application.earliest_doj" :min="today" required />
              </FormField>
              <FormField name="application.source" :error="errors['application.source']">
                <FormControl
                  label="How did you hear about this position?"
                  type="select"
                  v-model="data.application.source"
                  :options="['', ...form.sources]"
                  required
                />
              </FormField>
            </div>
          </Section>

          <Section title="Declaration">
            <p class="mb-3 whitespace-pre-line text-sm text-gray-700">{{ form.declaration }}</p>
            <FormField name="declaration" :error="errors.declaration">
              <label class="flex items-center gap-2 text-sm font-medium text-gray-900">
                <input v-model="data.declaration_accepted" type="checkbox" class="rounded border-gray-300" /> Yes, I agree.
              </label>
            </FormField>
          </Section>

          <div v-if="errorCount || submitError" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            <template v-if="errorCount">
              Please correct the {{ errorCount === 1 ? 'highlighted field' : `${errorCount} highlighted fields` }} above.
              <button type="button" class="ml-1 font-medium underline" @click="scrollToFirstError">Go to first</button>
            </template>
            <!-- Errors that belong to no single field, e.g. applications closed. -->
            <div v-else>{{ submitError }}</div>
          </div>

          <div class="sticky bottom-0 -mx-4 flex flex-wrap items-center justify-between gap-3 border-t bg-white/95 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-xl sm:border sm:px-5 sm:shadow-lg">
            <span class="text-xs text-gray-500">
              <template v-if="errorCount">{{ errorCount }} field{{ errorCount === 1 ? '' : 's' }} to fix</template>
              <template v-else>Please review your details. An application can be submitted only once.</template>
            </span>
            <Button variant="solid" size="lg" :loading="submitting" type="submit" icon-right="send">Submit Application</Button>
          </div>
        </form>
      </template>
    </div>
    <Dialog v-model="showInstructions" :options="{ size: '3xl' }">
      <template #body>
        <div class="flex max-h-[85vh] flex-col">
          <header class="flex shrink-0 items-start justify-between gap-3 bg-brand-700 px-6 py-4 text-white">
            <div class="min-w-0">
              <div class="text-xs font-semibold uppercase tracking-wider text-white/75">Important instructions</div>
              <h2 class="truncate text-lg font-bold">{{ job?.job_title }}</h2>
            </div>
            <button class="rounded-md p-1.5 text-white/80 hover:bg-white/15 hover:text-white" aria-label="Close" @click="showInstructions = false">
              <FeatherIcon name="x" class="h-5 w-5" />
            </button>
          </header>
          <div class="min-h-0 flex-1 overflow-y-auto px-6 py-5">
            <ul class="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <li v-for="fact in instructionFacts" :key="fact.label" class="flex items-start gap-3 rounded-lg bg-brand-50 px-3 py-2.5">
                <FeatherIcon :name="fact.icon" class="mt-0.5 h-4 w-4 shrink-0 text-brand-700" />
                <div class="min-w-0 text-sm">
                  <div class="text-xs text-gray-600">{{ fact.label }}</div>
                  <div class="font-semibold text-gray-900">{{ fact.value }}</div>
                </div>
              </li>
            </ul>
            <section v-if="form.instructions?.general" class="mt-6">
              <h3 class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">General</h3>
              <div class="prose prose-sm max-w-none text-gray-700" v-html="form.instructions.general" />
            </section>
            <section v-if="form.instructions?.job" class="mt-6">
              <h3 class="mb-2 text-xs font-bold uppercase tracking-wide text-brand-700">For this post</h3>
              <div class="prose prose-sm max-w-none text-gray-700" v-html="form.instructions.job" />
            </section>
          </div>
          <footer class="flex shrink-0 justify-end border-t bg-gray-50 px-6 py-3">
            <Button variant="solid" :class="BTN_BRAND" @click="showInstructions = false">I have read these — start</Button>
          </footer>
        </div>
      </template>
    </Dialog>
  </CandidatePortalLayout>
</template>

<script setup>
import BackButton from '@/components/common/BackButton.vue'
import { computed, h, nextTick, onMounted, provide, reactive, ref, watch } from 'vue'
import { Autocomplete, Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import dayjs from 'dayjs'
import CandidatePortalLayout from '@/layouts/CandidatePortalLayout.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import UploadField from '@/components/candidate/UploadField.vue'
import FormField from '@/components/candidate/FormField.vue'
import { validateApplication } from '@/utils/applicationValidation'
import { useJobOpeningDetail } from '@/composables/useJobOpenings'
import { useApplicationForm } from '@/composables/useApplications'

const props = defineProps({ id: { type: String, required: true } })

const { job, loading: jobLoading, fetchJob } = useJobOpeningDetail()
const { submitting, submit } = useApplicationForm()

const form = computed(
  () =>
    job.value?.form || {
      is_open: false,
      screening_questions: [],
      required_documents: [],
      sources: [],
      upload_rule: { formats: [], max_size_mb: 5 },
      sections: {},
      options: {},
    },
)
// Academic sections this job switches on, and their dropdown lists.
const sec = computed(() => form.value.sections || {})
const opt = computed(() => form.value.options || {})
const academicForm = computed(() => !!(sec.value.phd || sec.value.net || sec.value.publications))
const viewer = computed(() => job.value?.viewer || {})

const jobChips = computed(() =>
  [
    { icon: 'home', text: job.value?.department },
    { icon: 'briefcase', text: job.value?.employment_type },
    { icon: 'users', text: job.value?.vacancies ? `${job.value.vacancies} vacanc${job.value.vacancies == 1 ? 'y' : 'ies'}` : '' },
    { icon: 'award', text: job.value?.designation },
  ].filter((c) => c.text),
)

// Guests apply without an account: their uploads go to the application's
// own endpoint, and each returns a token sent back with the submission.
const uploadTokens = reactive(new Map())
provide('guestUpload', {
  enabled: computed(() => !viewer.value.logged_in),
  endpoint: computed(
    () => `/api/method/pathways.api.application.upload_application_file?job_opening=${encodeURIComponent(props.id)}`,
  ),
  tokens: uploadTokens,
})

// ----- form state
function emptyData() {
  return {
    candidate: { full_name: '', email: '', mobile_number: '', date_of_birth: '', gender: '', address: '', category: '' },
    application: {
      qualifications: [
        { degree_level: 'Undergraduate' },
        { degree_level: 'Postgraduate' },
        { degree_level: 'Doctoral' },
      ],
      // academic sections (sent only to jobs that ask for them; the server ignores the rest)
      specializations: [],
      other_specialization: '',
      disability_type: '',
      disability_percentage: '',
      phd_awarded: '',
      net_qualified: '',
      net_exam: '',
      net_subject: '',
      net_other_subject: '',
      net_award_date: '',
      net_roll_number: '',
      overall_experience_months: '',
      teaching_experience_months: '',
      research_experience_months: '',
      legal_experience_months: '',
      legal_experience_details: '',
      held_admin_responsibility: '',
      administrative_responsibilities: [{}],
      publications: [],
      overall_experience_years: '',
      relevant_experience_years: '',
      notice_period: '',
      employment_history: [{ is_current: false }],
      references: [{}, {}],
      resume_attachment: '',
      sop_attachment: '',
      additional_attachment: '',
      current_salary: '',
      expected_salary: '',
      earliest_doj: '',
      source: '',
    },
    declaration_accepted: false,
  }
}

const data = reactive(emptyData())
const answers = reactive({})
const documents = reactive({})

// ----- instructions (general from Settings, post-specific from the job,
// plus facts the app knows: deadline, time, file rules)
const showInstructions = ref(false)
const instructionFacts = computed(() => {
  const rule = form.value.upload_rule || {}
  return [
    form.value.application_deadline && {
      icon: 'clock',
      label: 'Deadline',
      value: `${dayjs(form.value.application_deadline).format('D MMM YYYY, h:mm A')} (IST)`,
    },
    { icon: 'watch', label: 'Time needed', value: academicForm.value ? 'About 90 minutes' : 'About 30 minutes' },
    {
      icon: 'paperclip',
      label: 'Uploads',
      value: `${(rule.formats || []).map((f) => f.toUpperCase()).join(', ') || 'PDF'} · up to ${rule.max_size_mb || 5} MB each`,
    },
  ].filter(Boolean)
})

const OTHER = '__other__'
const RANKS = [
  { field: 'qs_rank', label: 'QS' },
  { field: 'the_rank', label: 'THE' },
  { field: 'arwu_rank', label: 'ARWU' },
]
const MONTH_FIELDS = [
  { field: 'overall_experience_months', label: 'Overall work experience (months)', required: true },
  { field: 'teaching_experience_months', label: 'Teaching experience (months)', required: true },
  {
    field: 'research_experience_months',
    label: 'Research experience (months)',
    hint: 'Excluding PhD, internships and any stint shorter than 3 months.',
  },
  { field: 'legal_experience_months', label: 'Professional legal experience (months)', hint: 'Excluding internships.' },
]

const institutionOptions = computed(() => [
  ...(opt.value.institutions || []).map((name) => ({ label: name, value: name })),
  { label: 'Other (not in the list)', value: OTHER },
])
const netSubjectOptions = computed(() => (opt.value.net_subjects || []).map((name) => ({ label: name, value: name })))

function pickInstitution(q, value) {
  q._other = value === OTHER
  q.other_institution = value && value !== OTHER ? value : ''
}

// The PhD row lives in qualifications with the other degrees (added on
// load if an older draft has none).
const doctoral = computed(() => data.application.qualifications.find((q) => q.degree_level === 'Doctoral') || {})

// Publications start with as many rows as the job requires (at least one).
function ensurePublicationRows() {
  const want = Math.max(sec.value.min_publications || 0, sec.value.publications ? 1 : 0)
  while (data.application.publications.length < want) data.application.publications.push({})
}

// A university restored from a draft that is not in the list was typed under "Other".
function markOtherInstitutions() {
  const listed = new Set(opt.value.institutions || [])
  for (const q of data.application.qualifications) {
    if (q.degree_level !== 'Doctoral' && opt.value.institutions && q.other_institution && !listed.has(q.other_institution)) q._other = true
  }
}

function isRequiredDegree(q) {
  return q.degree_level === 'Undergraduate' || !!form.value.require_postgraduate
}

const age = computed(() => {
  const dob = data.candidate.date_of_birth
  if (!dob || !dayjs(dob).isValid()) return null
  const years = dayjs().diff(dayjs(dob), 'year')
  return years >= 0 && years < 120 ? years : null
})

function addEmployment() {
  data.application.employment_history.push({ is_current: false })
}

// ----- draft kept on this device only (convenience; never trusted)
const draftKey = computed(() => `pathways-apply-${props.id}-${viewer.value.email || 'guest'}`)

function saveDraft() {
  if (submitted.value) return
  try {
    localStorage.setItem(
      draftKey.value,
      JSON.stringify({ data, answers, documents, uploadTokens: Object.fromEntries(uploadTokens) }),
    )
  } catch {
    // storage unavailable — drafts are a convenience only
  }
}

function clearDraft() {
  try {
    localStorage.removeItem(draftKey.value)
  } catch {
    // ignore
  }
}

function restore() {
  Object.assign(data, emptyData())
  for (const key of Object.keys(answers)) delete answers[key]
  for (const key of Object.keys(documents)) delete documents[key]
  for (const q of form.value.screening_questions) answers[q.idx] = { idx: q.idx, answer: '', details: '' }

  // Prefill from the candidate's profile (earlier application), then any draft.
  const profile = viewer.value.profile
  if (profile) {
    for (const key of Object.keys(data.candidate)) data.candidate[key] = profile[key] || ''
  }
  try {
    const saved = JSON.parse(localStorage.getItem(draftKey.value) || 'null')
    if (saved?.data) {
      Object.assign(data.candidate, saved.data.candidate || {})
      Object.assign(data.application, saved.data.application || {})
      data.declaration_accepted = false
      for (const [idx, a] of Object.entries(saved.answers || {})) if (answers[idx]) Object.assign(answers[idx], a)
      Object.assign(documents, saved.documents || {})
      for (const [url, token] of Object.entries(saved.uploadTokens || {})) uploadTokens.set(url, token)
    }
  } catch {
    // corrupt or unavailable draft — start clean
  }
  if (!data.application.qualifications.some((q) => q.degree_level === 'Doctoral')) {
    data.application.qualifications.push({ degree_level: 'Doctoral' })
  }
  ensurePublicationRows()
  markOtherInstitutions()
}

let draftTimer = null
watch([() => data, answers, documents], () => {
  clearTimeout(draftTimer)
  draftTimer = setTimeout(saveDraft, 600)
}, { deep: true })

// ----- submit
const submitted = ref(false)
const applicationId = ref('')
const submittedEmail = ref('')
const submittedAt = ref('')
const copied = ref(false)

const NEXT_STEPS = [
  { title: 'Application received', text: 'We have your application and documents.' },
  { title: 'Screening', text: 'The recruitment team reviews eligibility and documents.' },
  { title: 'Shortlisting', text: 'Shortlisted candidates are contacted by email for the next round.' },
  { title: 'Interview & decision', text: 'Interview details and the final outcome are sent to your email.' },
]

async function copyApplicationId() {
  try {
    await navigator.clipboard.writeText(applicationId.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    // clipboard unavailable — the ID is shown on screen
  }
}
const submitError = ref('')

// Field errors: { fieldKey: message }, shown under each field. Checked in
// the browser first (utils/applicationValidation.js); the server re-checks
// and returns the same keys. After the first attempt they update live.
const errors = reactive({})
const attempted = ref(false)
const errorCount = computed(() => Object.keys(errors).length)
const today = dayjs().format('YYYY-MM-DD')

function setErrors(next) {
  for (const key of Object.keys(errors)) delete errors[key]
  Object.assign(errors, next)
}

function runChecks() {
  return validateApplication({ data, answers, documents, form: form.value, viewer: viewer.value })
}

watch([() => data, answers, documents], () => {
  if (attempted.value && !submitting.value) setErrors(runChecks())
}, { deep: true })

async function scrollToFirstError() {
  await nextTick()
  const first = [...document.querySelectorAll('[data-field]')].find((el) => errors[el.dataset.field])
  first?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  first?.querySelector('input, select, textarea, button')?.focus({ preventScroll: true })
}

async function handleSubmit() {
  submitError.value = ''
  attempted.value = true
  setErrors(runChecks())
  if (errorCount.value) return scrollToFirstError()

  const payload = {
    candidate: { ...data.candidate },
    application: {
      ...data.application,
      screening_answers: Object.values(answers),
      documents: Object.entries(documents)
        .filter(([, url]) => url)
        .map(([document_type, attachment]) => ({ document_type, attachment })),
    },
    declaration_accepted: data.declaration_accepted ? 1 : 0,
    upload_tokens: Object.fromEntries(uploadTokens),
  }
  try {
    const result = await submit(props.id, payload)
    applicationId.value = result.application_id
    submittedEmail.value = result.email
    submittedAt.value = dayjs().format('DD MMMM YYYY, h:mm A')
    submitted.value = true
    clearDraft()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    setErrors(e?.fieldErrors || {})
    if (errorCount.value) return scrollToFirstError()
    submitError.value = e?.messages?.[0] || 'Something went wrong. Please try again.'
  }
}

function formatDateTime(value) {
  return dayjs(value).format('DD MMMM YYYY, h:mm A')
}

async function load(id) {
  submitted.value = false
  submitError.value = ''
  attempted.value = false
  setErrors({})
  await fetchJob(id)
  if (job.value) restore()
}

onMounted(() => load(props.id))
watch(() => props.id, load)

const Section = (p, { slots }) =>
  h('section', { class: 'rounded-xl border bg-white p-5 shadow-sm sm:p-6 [counter-increment:section]' }, [
    h('div', { class: 'mb-5 flex items-start gap-3 border-b pb-4' }, [
      // Numbered automatically (CSS counter), so optional sections never leave gaps.
      h('span', {
        class:
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-700 text-xs font-bold text-white before:content-[counter(section)]",
      }),
      h('div', [
        h('div', { class: 'flex items-center gap-2' }, [
          h('h2', { class: 'text-base font-bold text-gray-900' }, p.title),
          p.badge ? h('span', { class: 'rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600' }, p.badge) : null,
        ]),
        p.subtitle ? h('p', { class: 'mt-0.5 text-sm text-gray-500' }, p.subtitle) : null,
      ]),
    ]),
    slots.default?.(),
  ])
Section.props = ['title', 'subtitle', 'badge']

// A required Yes / No question as two radio buttons.
const YesNo = (p, { emit }) =>
  h('div', [
    h('div', { class: 'mb-1.5 text-sm text-gray-800' }, [p.label, h('span', { class: 'text-red-500' }, ' *')]),
    h(
      'div',
      { class: 'flex gap-5' },
      ['Yes', 'No'].map((value) =>
        h('label', { class: 'flex items-center gap-2 text-sm text-gray-700' }, [
          h('input', {
            type: 'radio',
            value,
            checked: p.modelValue === value,
            onChange: () => emit('update:modelValue', value),
          }),
          value,
        ]),
      ),
    ),
  ])
YesNo.props = ['modelValue', 'label']
YesNo.emits = ['update:modelValue']
</script>
