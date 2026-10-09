<template>
  <!-- Choose which documents of the chosen candidates each panellist of the
       job's Selection Committee gets. Ticks already shared start ticked;
       only the cells you change are saved. -->
  <Dialog :model-value="open" :options="{ title: 'Share documents with the panel', size: '4xl' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div v-if="state.loading" class="h-56 animate-pulse rounded-lg bg-gray-100" />
      <p v-else-if="state.error" class="whitespace-pre-line rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{{ state.error }}</p>
      <div v-else-if="options" class="flex flex-col gap-4 text-sm">
        <div class="rounded-lg border bg-gray-50 px-3 py-2">
          <div class="font-medium text-gray-900">
            {{ options.job.job_title }}<span v-if="options.job.position" class="text-gray-500"> · {{ options.job.position }}</span>
          </div>
          <div class="mt-0.5 text-xs text-gray-600">
            {{ options.applications.length === 1 ? options.applications[0].candidate_name + ' · ' + options.applications[0].application_id : `${options.applications.length} candidates: ${candidateList}` }}
          </div>
        </div>

        <div v-if="!options.panel.length" class="rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-orange-800">
          This job has no Selection Committee yet. Set up the panel on the job's Interviews tab first.
        </div>
        <div v-else-if="!options.documents.length" class="rounded-lg border border-dashed px-3 py-6 text-center text-gray-500">
          {{ options.applications.length === 1 ? 'This candidate has' : 'These candidates have' }} not uploaded any documents.
        </div>
        <template v-else>
          <div class="flex flex-wrap items-center gap-2 text-xs text-gray-600">
            <span>
              Check the documents each panellist should see. Documents already shared are checked.
              <template v-if="options.applications.length > 1"> A dash means shared for some of the candidates.</template>
            </span>
            <div class="ml-auto flex gap-1">
              <Button size="sm" variant="outline" @click="setAll(true)">Check all</Button>
              <Button size="sm" variant="outline" @click="setAll(false)">Uncheck all</Button>
            </div>
          </div>
          <div class="max-h-[50vh] overflow-auto rounded-lg border">
            <table class="w-full text-sm">
              <thead class="sticky top-0 z-10 bg-gray-50 text-xs text-gray-600">
                <tr>
                  <th class="px-3 py-2 text-left font-medium">Document</th>
                  <th v-for="p in options.panel" :key="p.user" class="min-w-[7rem] border-l px-2 py-2 text-center font-medium">
                    <div class="truncate" :title="p.user">{{ p.full_name }}</div>
                    <label class="mt-1 inline-flex cursor-pointer items-center gap-1 font-normal text-gray-500">
                      <input
                        type="checkbox"
                        class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                        :checked="columnState(p.user) === true"
                        :indeterminate.prop="columnState(p.user) === 'some'"
                        :aria-label="`All documents for ${p.full_name}`"
                        @change="setColumn(p.user, $event.target.checked)"
                      />
                      All
                    </label>
                  </th>
                </tr>
              </thead>
              <tbody>
                <template v-for="g in groups" :key="g.group">
                  <tr class="bg-gray-50/60">
                    <td :colspan="options.panel.length + 1" class="px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-gray-500">{{ g.group }}</td>
                  </tr>
                  <tr v-for="d in g.documents" :key="d.label" class="border-t">
                    <td class="px-3 py-1.5">
                      <label class="flex cursor-pointer items-center gap-2">
                        <input
                          type="checkbox"
                          class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                          :checked="rowState(d.label) === true"
                          :indeterminate.prop="rowState(d.label) === 'some'"
                          :aria-label="`${d.label} for every panellist`"
                          @change="setRow(d.label, $event.target.checked)"
                        />
                        <span class="text-gray-900">{{ d.label }}</span>
                        <span v-if="options.applications.length > 1" class="text-xs text-gray-400">{{ d.count }} of {{ options.applications.length }}</span>
                      </label>
                    </td>
                    <td v-for="p in options.panel" :key="p.user" class="border-l px-2 py-1.5 text-center">
                      <input
                        type="checkbox"
                        class="rounded border-gray-300 text-brand-700 focus:ring-brand-700"
                        :checked="cell(p.user, d.label) === true"
                        :indeterminate.prop="cell(p.user, d.label) === 'some'"
                        :aria-label="`${d.label} for ${p.full_name}`"
                        @change="setCell(p.user, d.label, $event.target.checked)"
                      />
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <FormControl v-model="form.note" label="Note to the panel (optional)" type="textarea" :rows="2" placeholder="e.g. Please read the writing samples before Monday's interviews." />
          <label class="flex items-start gap-2.5">
            <input v-model="form.notify" type="checkbox" class="mt-0.5 rounded border-gray-300 text-brand-700 focus:ring-brand-700" />
            <span>
              Email each panellist who gets new documents
              <span class="block text-xs text-gray-500">One email per panellist, listing the candidates and documents with a link to view them after logging in. Files are not attached.</span>
            </span>
          </label>
          <p v-if="form.error" class="whitespace-pre-line rounded-md bg-red-50 px-3 py-2 text-red-700">{{ form.error }}</p>
        </template>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <span v-if="changeCount" class="mr-auto text-xs text-gray-500">{{ changeCount }} change{{ changeCount === 1 ? '' : 's' }}</span>
        <Button variant="ghost" @click="emit('update:open', false)">Close</Button>
        <Button
          variant="solid"
          :class="BTN_BRAND"
          icon-left="share-2"
          :loading="form.saving"
          :disabled="!changeCount || !options?.panel.length"
          @click="save"
        >
          Save sharing
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FormControl } from 'frappe-ui'
import { panelService } from '@/services/panel'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  open: { type: Boolean, default: false },
  // Application names (one job opening)
  applications: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:open', 'saved'])

const options = ref(null)
const state = reactive({ loading: false, error: '' })
const form = reactive({ note: '', notify: true, saving: false, error: '' })
// { panelist: { label: true | false } }: only the cells the user changed
const changes = ref({})

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    Object.assign(form, { note: '', notify: true, saving: false, error: '' })
    changes.value = {}
    await load()
  },
)

async function load() {
  options.value = null
  state.loading = true
  state.error = ''
  try {
    options.value = await panelService.getShareOptions(props.applications)
  } catch (e) {
    state.error = e?.messages?.join('\n') || 'Could not load the panel and documents.'
  } finally {
    state.loading = false
  }
}

const candidateList = computed(() => {
  const names = (options.value?.applications || []).map((a) => a.candidate_name || a.application_id)
  return names.length > 4 ? `${names.slice(0, 4).join(', ')} and ${names.length - 4} more` : names.join(', ')
})
const groups = computed(() => {
  const out = []
  for (const d of options.value?.documents || []) {
    let g = out.find((x) => x.group === d.group)
    if (!g) out.push((g = { group: d.group, documents: [] }))
    g.documents.push(d)
  }
  return out
})
const docCount = computed(() => Object.fromEntries((options.value?.documents || []).map((d) => [d.label, d.count])))

// What is shared now: true (for every candidate who has it), 'some', or false
function initial(user, label) {
  const n = options.value?.shared?.[user]?.[label] || 0
  if (!n) return false
  return n >= (docCount.value[label] || 0) ? true : 'some'
}
function cell(user, label) {
  const c = changes.value[user]
  return c && label in c ? c[label] : initial(user, label)
}
function setCell(user, label, on) {
  const next = { ...changes.value, [user]: { ...(changes.value[user] || {}) } }
  // Back to how it was: not a change any more.
  if (initial(user, label) === on) delete next[user][label]
  else next[user][label] = on
  if (!Object.keys(next[user]).length) delete next[user]
  changes.value = next
}
const labels = computed(() => (options.value?.documents || []).map((d) => d.label))
const users = computed(() => (options.value?.panel || []).map((p) => p.user))
function summarise(values) {
  if (values.length && values.every((v) => v === true)) return true
  return values.some((v) => v) ? 'some' : false
}
const columnState = (user) => summarise(labels.value.map((l) => cell(user, l)))
const rowState = (label) => summarise(users.value.map((u) => cell(u, label)))
const setColumn = (user, on) => labels.value.forEach((l) => setCell(user, l, on))
const setRow = (label, on) => users.value.forEach((u) => setCell(u, label, on))
const setAll = (on) => users.value.forEach((u) => setColumn(u, on))
const changeCount = computed(() => Object.values(changes.value).reduce((n, c) => n + Object.keys(c).length, 0))

async function save() {
  form.saving = true
  form.error = ''
  try {
    const r = await panelService.shareWithPanel(props.applications, changes.value, form.note.trim(), form.notify)
    const parts = []
    if (r.added) parts.push(`${r.added} document${r.added === 1 ? '' : 's'} shared with ${r.panellists} panellist${r.panellists === 1 ? '' : 's'}`)
    if (r.removed) parts.push(`${r.removed} no longer shared`)
    toast({ title: parts.length ? parts.join(' · ') + '.' : 'Nothing to change.', icon: 'check', iconClasses: 'text-green-500' })
    if (form.notify && r.panellists && !r.emailed) {
      toast({ title: 'No email sent: the "Candidate documents shared" email is turned off in Email Setup.', icon: 'alert-triangle', iconClasses: 'text-orange-500' })
    }
    emit('saved')
    emit('update:open', false)
  } catch (e) {
    form.error = e?.messages?.join('\n') || 'Could not save the sharing.'
  } finally {
    form.saving = false
  }
}
</script>
