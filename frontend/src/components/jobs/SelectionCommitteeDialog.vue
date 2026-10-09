<template>
  <!-- Set up or edit a job's Selection Committee (workflow step 15). Loads
       the current committee itself, so any page can open it. -->
  <Dialog :model-value="open" :options="{ title: title, size: '2xl' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div class="flex flex-col gap-4 text-sm">
        <div v-if="loading" class="text-gray-500">Loading…</div>
        <template v-else>
          <p class="text-gray-600">
            <template v-if="jobTitle"><b class="text-gray-900">{{ jobTitle }}</b> · </template>
            Choose {{ size.min }}–{{ size.max }} panellists. They see only this job's interview candidates, and new panellists get an invitation email.
          </p>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <FormControl label="Interview date" type="date" v-model="state.date" />
            <FormControl label="Start time" type="time" v-model="state.time" />
          </div>
          <div class="flex flex-col gap-2">
            <div
              v-for="(row, i) in state.members"
              :key="i"
              class="grid grid-cols-1 items-end gap-2 rounded-lg border p-3 sm:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)_auto_auto]"
            >
              <label class="flex flex-col gap-1 text-xs text-gray-600">
                Panellist
                <select v-model="row.member" class="h-8 rounded border-gray-200 bg-gray-100 text-sm">
                  <option value="">Choose…</option>
                  <option v-for="u in availableUsers(row.member)" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
                </select>
              </label>
              <FormControl label="Role on the panel" v-model="row.designation_label" placeholder="e.g. Chairperson, Subject expert" />
              <label class="flex h-8 items-center gap-2 text-sm text-gray-700">
                <input v-model="row.is_external_expert" type="checkbox" class="rounded border-gray-300 text-brand-700 focus:ring-brand-700" />External
              </label>
              <Button variant="ghost" icon="trash-2" :aria-label="`Remove panellist ${i + 1}`" @click="state.members.splice(i, 1)" />
            </div>
          </div>
          <Button
            class="self-start"
            variant="outline"
            icon-left="plus"
            :disabled="state.members.length >= size.max"
            @click="state.members.push({ member: '', designation_label: '', is_external_expert: false })"
          >
            Add panellist
          </Button>
        </template>
        <p v-if="!loading && chosenCount < size.min" class="flex items-center gap-1.5 text-orange-700">
          <FeatherIcon name="info" class="h-4 w-4 shrink-0" />
          Choose at least {{ size.min }} panellists to save ({{ chosenCount }} chosen{{ state.members.length < size.min ? ' · use Add panellist' : '' }}).
        </p>
        <p v-if="state.error" class="rounded-md bg-red-50 px-3 py-2 text-red-700">{{ state.error }}</p>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="emit('update:open', false)">Cancel</Button>
        <Button variant="solid" :class="BTN_BRAND" :loading="state.saving" :disabled="loading || chosenCount < size.min" @click="save">
          Save committee ({{ chosenCount }})
        </Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, FeatherIcon, FormControl } from 'frappe-ui'
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

function availableUsers(current) {
  const taken = new Set(state.members.map((m) => m.member).filter((m) => m && m !== current))
  return users.value.filter((u) => !taken.has(u.name))
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
        members: c
          ? c.members.map((m) => ({ member: m.member, designation_label: m.designation_label || '', is_external_expert: !!m.is_external_expert }))
          : Array.from({ length: size.min }, () => ({ member: '', designation_label: '', is_external_expert: false })),
      })
    } catch (e) {
      state.error = e?.messages?.[0] || 'Could not load the committee.'
    } finally {
      loading.value = false
    }
  },
)

async function save() {
  state.saving = true
  state.error = ''
  try {
    const committee = await interviewService.saveSelectionCommittee(
      props.jobOpening,
      state.members.filter((m) => m.member).map((m) => ({ ...m, is_external_expert: m.is_external_expert ? 1 : 0 })),
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
