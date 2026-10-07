<template>
  <!-- A job's shortlisting sheet(s), as in the workflow folder, with an Excel download. -->
  <Dialog v-model="isOpen" :options="{ size: '7xl' }">
    <template #body>
      <div class="flex max-h-[88vh] flex-col">
        <div class="flex flex-wrap items-start justify-between gap-3 border-b px-6 py-4">
          <div>
            <div class="text-xs font-bold uppercase tracking-wide text-brand-700">Shortlisting sheet · {{ track || report?.track }}</div>
            <h2 class="mt-0.5 text-xl font-semibold text-gray-900">{{ jobTitle || report?.job_title }}</h2>
          </div>
          <div class="flex items-center gap-2">
            <a :href="scoringService.shortlistingReportUrl(jobOpening)">
              <Button variant="solid" icon-left="download" :class="BTN_BRAND">Download Excel</Button>
            </a>
            <Button variant="ghost" icon="x" @click="isOpen = false" />
          </div>
        </div>
        <div v-if="report?.sheets?.length > 1" class="flex gap-1 border-b px-4">
          <button
            v-for="(sh, i) in report.sheets"
            :key="sh.title"
            type="button"
            class="relative px-3 py-2.5 text-sm"
            :class="sheetIdx === i ? 'font-semibold text-brand-700' : 'text-gray-600 hover:text-gray-900'"
            @click="sheetIdx = i"
          >
            {{ sh.title }} <span class="ml-1 rounded-full bg-gray-100 px-1.5 text-xs">{{ sh.rows.length }}</span>
            <span v-if="sheetIdx === i" class="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-brand-700" />
          </button>
        </div>
        <div class="min-h-0 flex-1 overflow-auto">
          <div v-if="reportLoading" class="p-10 text-center text-sm text-gray-500">Loading…</div>
          <div v-else-if="reportError" class="m-6 rounded-md bg-red-50 p-3 text-sm text-red-700">{{ reportError }}</div>
          <table v-else-if="sheet" class="min-w-full border-separate border-spacing-0 text-sm">
            <thead class="sticky top-0 z-10">
              <tr>
                <th
                  v-for="col in sheet.columns"
                  :key="col"
                  class="min-w-[9rem] max-w-[16rem] border-b bg-brand-700 px-3 py-2 text-left align-top text-xs font-semibold text-white"
                >{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!sheet.rows.length"><td :colspan="sheet.columns.length" class="px-4 py-8 text-center text-gray-500">No candidates on this sheet yet.</td></tr>
              <tr v-for="(row, r) in sheet.rows" :key="r" class="odd:bg-white even:bg-gray-50">
                <td v-for="(v, c) in row" :key="c" class="max-w-[16rem] border-b px-3 py-2 align-top text-gray-800">
                  <a v-if="typeof v === 'string' && v.startsWith('http')" :href="v" target="_blank" rel="noopener" class="text-brand-700 hover:underline">Open</a>
                  <span v-else class="line-clamp-3 whitespace-pre-line" :title="String(v)">{{ v }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog } from 'frappe-ui'
import { scoringService } from '@/services/scoring'
import { BTN_BRAND } from '@/utils/buttonStyles'

const props = defineProps({
  open: { type: Boolean, default: false },
  jobOpening: { type: String, default: '' },
  jobTitle: { type: String, default: '' },
  track: { type: String, default: '' },
})
const emit = defineEmits(['update:open'])

const isOpen = computed({
  get: () => props.open,
  set: (v) => emit('update:open', v),
})

const report = ref(null)
const reportLoading = ref(false)
const reportError = ref('')
const sheetIdx = ref(0)
const sheet = computed(() => report.value?.sheets?.[sheetIdx.value])

watch(
  () => [props.open, props.jobOpening],
  async ([open, job]) => {
    if (!open || !job) return
    report.value = null
    reportLoading.value = true
    reportError.value = ''
    sheetIdx.value = 0
    try {
      report.value = await scoringService.getShortlistingReport(job)
    } catch (e) {
      reportError.value = e?.messages?.[0] || 'Could not load the shortlisting sheet.'
    } finally {
      reportLoading.value = false
    }
  },
)
</script>
