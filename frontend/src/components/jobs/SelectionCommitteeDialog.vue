<template>
  <!-- Set up or edit a job's Selection Committee (workflow step 15). Loads
       the current committee itself, so any page can open it. -->
  <!-- Same width as the Schedule dialog it opens from, so nothing shifts. -->
  <Dialog :model-value="open" :options="{ title: title, size: '2xl' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div class="flex flex-col gap-5 text-sm">
        <div v-if="loading" class="flex flex-col gap-3" aria-busy="true">
          <div class="h-16 animate-pulse rounded-xl bg-gray-50" />
          <div v-for="i in 3" :key="i" class="h-14 animate-pulse rounded-xl bg-gray-50" />
        </div>

        <template v-else>
          <p class="text-p-sm text-gray-600">
            <template v-if="jobTitle"><b class="font-semibold text-gray-900">{{ jobTitle }}</b> · </template>
            Panellists see only this job's interview candidates. New panellists get an invitation email.
          </p>

          <!-- When, and how many -->
          <div class="grid grid-cols-1 gap-4 rounded-xl border bg-gray-50/60 p-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_9rem]">
            <FormControl label="Interview date" type="date" v-model="state.date" />
            <FormControl label="Start time" type="time" v-model="state.time" />
            <div>
              <!-- The range comes from Settings › General (selection committee
                   min/max), so larger panels need no code change. -->
              <FormControl
                label="Panel size"
                type="select"
                :model-value="String(panelSize)"
                :options="sizeOptions"
                @update:model-value="(v) => setPanelSize(Number(v))"
              />
            </div>
          </div>

          <!-- Panellists: nobody until people are added -->
          <div>
            <div class="mb-2 flex items-center justify-between gap-3">
              <h3 class="text-sm font-semibold text-gray-900">Panellists</h3>
              <span class="rounded-full px-2.5 py-0.5 text-xs font-medium tabular-nums" :class="allChosen ? 'bg-brand-50 text-brand-700' : 'bg-gray-100 text-gray-600'">
                {{ state.members.length }} of {{ panelSize }}
              </span>
            </div>

            <UserPicker
              :users="users"
              :exclude="state.members.map((m) => m.member)"
              :disabled="state.members.length >= panelSize"
              :placeholder="state.members.length >= panelSize ? `Panel is full: choose a larger panel size to add more` : 'Search staff by name or email to add a panellist'"
              @select="addMember"
            />

            <div v-if="!state.members.length" class="mt-3 flex flex-col items-center gap-1 rounded-xl border border-dashed px-4 py-7 text-center">
              <FeatherIcon name="users" class="h-5 w-5 text-gray-400" />
              <p class="text-sm font-medium text-gray-700">No panellists yet</p>
              <p class="text-xs text-gray-500">Search above to add {{ panelSize }} people to the panel.</p>
            </div>

            <ul v-else class="mt-3 divide-y overflow-hidden rounded-xl border">
              <li v-for="(row, i) in state.members" :key="row.key" class="flex flex-wrap items-center gap-3 px-3 py-2.5 sm:flex-nowrap">
                <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
                  {{ initialsOf(row.member) }}
                </span>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-medium text-gray-900">
                    {{ nameOf(row.member) }}
                    <span v-if="row.is_external_expert && row.designation_label !== EXTERNAL" class="ml-1 text-xs font-normal text-gray-500">· External</span>
                  </p>
                  <p v-if="emailOf(row.member)" class="truncate text-xs text-gray-500">{{ emailOf(row.member) }}</p>
                </div>
                <select
                  v-model="row.designation_label"
                  @change="row.is_external_expert = row.designation_label === EXTERNAL"
                  class="h-8 w-40 shrink-0 rounded-lg border-gray-200 bg-gray-50 py-0 pl-2.5 pr-8 text-sm text-gray-800 focus:border-brand-500 focus:ring-brand-500"
                  :aria-label="`Role of ${nameOf(row.member)}`"
                >
                  <option v-for="r in roleOptions(row.designation_label)" :key="r.value" :value="r.value">{{ r.label }}</option>
                </select>
                <Button variant="ghost" icon="x" :aria-label="`Remove ${nameOf(row.member)}`" title="Remove" @click="state.members.splice(i, 1)" />
              </li>
            </ul>
          </div>
        </template>

        <p v-if="state.error" class="rounded-lg bg-red-50 px-3 py-2 text-red-700" role="alert">{{ state.error }}</p>
      </div>
    </template>
    <template #actions>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="flex items-center gap-1.5 text-sm text-amber-700">
          <template v-if="!loading && !allChosen">
            <FeatherIcon name="info" class="h-4 w-4 shrink-0" />
            <template v-if="remaining > 0">Add {{ remaining }} more {{ remaining === 1 ? 'panellist' : 'panellists' }} to save.</template>
            <!-- An older committee can be larger than the size now allowed. -->
            <template v-else>Remove {{ -remaining }} {{ remaining === -1 ? 'panellist' : 'panellists' }}: at most {{ size.max }} allowed.</template>
          </template>
        </p>
        <div class="flex gap-2">
          <Button variant="ghost" @click="emit('update:open', false)">Cancel</Button>
          <Button variant="solid" :class="BTN_BRAND" :loading="state.saving" :disabled="loading || !allChosen" @click="save">
            Save committee
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
import UserPicker from '@/components/common/UserPicker.vue'
import { interviewService } from '@/services/interviews'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'

const props = defineProps({
  open: { type: Boolean, default: false },
  jobOpening: { type: String, default: '' },
  jobTitle: { type: String, default: '' },
})
const emit = defineEmits(['update:open', 'saved'])

const loading = ref(false)
const existing = ref(null)
const size = reactive({ min: 3, max: 5 })
const users = ref([])
const state = reactive({ date: '', time: '', members: [], saving: false, error: '' })
const title = computed(() => (existing.value ? 'Edit Selection Committee' : 'Set up Selection Committee'))
const chosenCount = computed(() => new Set(state.members.map((m) => m.member).filter(Boolean)).size)

// Roles offered on the panel; a custom role already saved stays selectable.
// "External expert" also sets the member's External flag (shown as a badge
// on the job's committee); there is no separate External switch.
const EXTERNAL = 'External expert'
const ROLES = ['Member', 'Chairperson', 'Subject expert', EXTERNAL, 'Member secretary']
function roleOptions(current) {
  const list = current && !ROLES.includes(current) ? [current, ...ROLES] : ROLES
  return list.map((r) => ({ label: r, value: r }))
}

// Panel size is the target; members are only the people added so far.
const panelSize = ref(3)
const allChosen = computed(() => state.members.length === panelSize.value && chosenCount.value === panelSize.value)
// Sizes from Settings › General; below the number already added is not offered.
const sizeOptions = computed(() => {
  const out = []
  for (let n = Math.max(size.min, state.members.length); n <= size.max; n++) {
    out.push({ label: `${n} ${n === 1 ? 'panellist' : 'panellists'}`, value: String(n) })
  }
  // An older committee larger than the allowed maximum still shows its size.
  if (!out.length) out.push({ label: `${panelSize.value} panellists`, value: String(panelSize.value) })
  return out
})
const remaining = computed(() => panelSize.value - state.members.length)
function setPanelSize(n) {
  panelSize.value = Math.min(Math.max(n, size.min, state.members.length), size.max)
}

let rowKey = 0
function addMember(user) {
  if (state.members.length >= panelSize.value || state.members.some((m) => m.member === user.name)) return
  state.members.push({ key: ++rowKey, member: user.name, designation_label: 'Member', is_external_expert: false })
}

const userByName = computed(() => Object.fromEntries(users.value.map((u) => [u.name, u])))
const nameOf = (name) => userByName.value[name]?.full_name || name
function emailOf(name) {
  const email = userByName.value[name]?.email || name
  return email !== nameOf(name) ? email : ''
}
function initialsOf(name) {
  const words = nameOf(name).replace(/@.*/, '').split(/[\s._-]+/).filter(Boolean)
  return words.slice(0, 2).map((w) => w[0].toUpperCase()).join('') || '?'
}

watch(
  () => props.open,
  async (open) => {
    if (!open || !props.jobOpening) return
    loading.value = true
    state.error = ''
    try {
      const [data, options] = await Promise.all([
        interviewService.getJobInterviews(props.jobOpening),
        users.value.length ? Promise.resolve(users.value) : interviewService.getPanelOptions(),
      ])
      users.value = options
      existing.value = data.committee
      Object.assign(size, data.committee_size)
      const c = data.committee
      Object.assign(state, {
        date: c?.scheduled_date || '',
        time: c?.scheduled_time ? c.scheduled_time.slice(0, 5) : '',
        members: (c?.members || []).map((m) => ({
          key: ++rowKey,
          member: m.member,
          // An external member saved without a role shows as External expert.
          designation_label: m.designation_label || (m.is_external_expert ? EXTERNAL : 'Member'),
          is_external_expert: !!m.is_external_expert,
        })),
      })
      // Editing keeps the committee's own size; a new one starts at the minimum.
      panelSize.value = Math.min(Math.max(state.members.length || size.min, size.min), size.max)
    } catch (e) {
      state.error = e?.messages?.[0] || 'Could not load the committee.'
    } finally {
      loading.value = false
    }
  },
)

async function save() {
  if (state.saving || !allChosen.value) return
  state.saving = true
  state.error = ''
  try {
    const committee = await interviewService.saveSelectionCommittee(
      props.jobOpening,
      state.members
        .filter((m) => m.member)
        .map((m) => ({ member: m.member, designation_label: (m.designation_label || '').trim(), is_external_expert: m.is_external_expert ? 1 : 0 })),
      state.date,
      state.time,
    )
    emit('update:open', false)
    toast({ title: 'Selection committee saved.', icon: 'check', iconClasses: 'text-green-500' })
    emit('saved', committee)
  } catch (e) {
    state.error = e?.messages?.[0] || 'Could not save the committee.'
  } finally {
    state.saving = false
  }
}
</script>
