<template>
  <!-- How applications are tied to a candidate, as a table of situations. -->
  <details class="group rounded-xl border border-blue-100 bg-blue-50/60 text-sm text-blue-900" :open="open">
    <summary class="flex cursor-pointer list-none items-center gap-2 px-4 py-3 font-medium">
      <FeatherIcon name="info" class="h-4 w-4 shrink-0" />
      How candidates are identified
      <span class="font-normal text-blue-900/70">· one candidate per email address</span>
      <FeatherIcon name="chevron-down" class="ml-auto h-4 w-4 transition group-open:rotate-180" />
    </summary>
    <div class="px-4 pb-4">
      <div class="overflow-x-auto rounded-lg border border-blue-100 bg-white">
        <table class="w-full text-sm text-gray-800">
          <thead class="bg-blue-50/80 text-left text-xs uppercase text-blue-900/80">
            <tr>
              <th class="px-3 py-2 font-semibold">Situation</th>
              <th class="w-28 px-3 py-2 font-semibold">Allowed?</th>
              <th class="px-3 py-2 font-semibold">What happens</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-blue-50">
            <tr v-for="r in RULES" :key="r.situation" class="align-top">
              <td class="px-3 py-2 font-medium">{{ r.situation }}</td>
              <td class="px-3 py-2">
                <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold" :class="TONE[r.allowed]">
                  <FeatherIcon :name="ICON[r.allowed]" class="h-3 w-3" />{{ r.allowed }}
                </span>
              </td>
              <td class="px-3 py-2 text-gray-700">{{ r.result }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="mt-2 text-xs text-blue-900/80">
        Emails are compared ignoring spaces and capital letters. The Candidate ID (PWY-CAND-…) is given on the first application and never
        changes; the email is also the candidate portal login.
      </p>
    </div>
  </details>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

defineProps({ open: { type: Boolean, default: false } })

const RULES = [
  {
    situation: 'Same email, different position',
    allowed: 'Yes',
    result: 'Added to the same candidate (same Candidate ID); all their applications show together.',
  },
  {
    situation: 'Same email, same position again',
    allowed: 'No',
    result: '"An application from this email address for this position already exists."',
  },
  {
    situation: 'Same email, same position, earlier one withdrawn',
    allowed: 'Yes',
    result: 'A new application to the same candidate.',
  },
  {
    situation: 'Applies signed in to the candidate portal',
    allowed: 'Yes',
    result: 'Uses the login email; the profile (mobile, address…) is updated from the new form.',
  },
  {
    situation: 'Applies without signing in, with an existing email',
    allowed: 'Yes',
    result: 'Goes to that candidate, but the profile is not changed. The acknowledgement goes to that email.',
  },
  {
    situation: 'Imported by the recruitment team',
    allowed: 'Yes',
    result: 'Matched by email the same way; an existing profile is never overwritten.',
  },
  {
    situation: 'A staff email (Pathways / Desk user)',
    allowed: 'No',
    result: '"Staff email addresses cannot be used to apply. Please use your personal email address."',
  },
  {
    situation: 'Same person, different email',
    allowed: 'Separate',
    result: 'Becomes a second candidate. If the mobile number matches, both are flagged "same mobile".',
  },
]
const TONE = { Yes: 'bg-green-50 text-green-700', No: 'bg-red-50 text-red-700', Separate: 'bg-amber-50 text-amber-800' }
const ICON = { Yes: 'check', No: 'x', Separate: 'copy' }
</script>
