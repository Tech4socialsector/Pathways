<template>
  <!-- Set up a job's Shortlisting Committee (workflow steps 7-8). -->
  <Dialog :model-value="open" :options="{ title: 'Set up Shortlisting Committee', size: 'lg' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-gray-600">
          Pick {{ state.min }}–{{ state.max }} members who will shortlist for this job. They get the Shortlisting Committee
          Member role and see only this job's applications.
        </p>
        <div v-if="state.loading" class="text-sm text-gray-500">Loading staff...</div>
        <div v-else class="max-h-64 overflow-y-auto rounded-lg border">
          <label
            v-for="u in state.users"
            :key="u.name"
            class="flex cursor-pointer items-center gap-3 border-b px-3 py-2 text-sm last:border-0 hover:bg-gray-50"
          >
            <input
              v-model="state.members"
              type="checkbox"
              :value="u.name"
              :disabled="!state.members.includes(u.name) && state.members.length >= state.max"
              class="rounded border-gray-300"
            />
            <span class="flex-1">
              <span class="font-medium text-gray-900">{{ u.full_name || u.name }}</span>
              <span class="block text-xs text-gray-500">{{ u.name }}</span>
            </span>
          </label>
        </div>
        <FormControl label="Office Order Reference (optional)" v-model="state.officeOrder" placeholder="e.g. NLSIU/OO/2026/45" />
        <ErrorMessage :message="state.error" />
      </div>
    </template>
    <template #actions>
      <Button variant="solid" :class="BTN_BRAND" :loading="state.saving" :disabled="state.members.length < state.min" @click="create">
        Create committee ({{ state.members.length }} selected)
      </Button>
    </template>
  </Dialog>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { Button, Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'
import { toast } from '@/utils/notify'
import { scoringService } from '@/services/scoring'

const props = defineProps({
  open: { type: Boolean, default: false },
  jobOpening: { type: String, required: true },
})
const emit = defineEmits(['update:open', 'created'])

const state = reactive({ loading: false, saving: false, users: [], members: [], min: 2, max: 3, officeOrder: '', error: '' })

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    Object.assign(state, { loading: true, members: [], officeOrder: '', error: '' })
    try {
      const options = await scoringService.getCommitteeOptions()
      Object.assign(state, { users: options.users, min: options.min, max: options.max })
    } catch (e) {
      state.error = e?.messages?.[0] || 'Could not load staff.'
    } finally {
      state.loading = false
    }
  },
)

async function create() {
  state.saving = true
  state.error = ''
  try {
    await scoringService.createShortlistingCommittee(props.jobOpening, state.members, state.officeOrder)
    emit('update:open', false)
    toast({ title: 'Shortlisting Committee created.', icon: 'check', iconClasses: 'text-green-500' })
    emit('created')
  } catch (e) {
    state.error = e?.messages?.[0] || 'Could not create the committee.'
  } finally {
    state.saving = false
  }
}
</script>
