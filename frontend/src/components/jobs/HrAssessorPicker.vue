<template>
  <!-- Round 1 (HR interaction): the people who take the interview and fill
       the HR assessment sheet (workflow step 13). v-model: user IDs. -->
  <div class="flex flex-col gap-1.5">
    <div class="flex items-baseline justify-between">
      <span class="text-xs font-medium text-gray-700">HR assessors</span>
      <span class="text-xs text-gray-500">{{ modelValue.length }} of {{ limit }}</span>
    </div>
    <ul v-if="modelValue.length" class="flex flex-wrap gap-1.5">
      <li v-for="u in modelValue" :key="u" class="flex items-center gap-1 rounded-full border border-brand-200 bg-brand-50 py-0.5 pl-2.5 pr-1 text-xs text-brand-800">
        {{ nameOf(u) }}
        <button type="button" class="rounded-full p-0.5 hover:bg-brand-100" :aria-label="`Remove ${nameOf(u)}`" @click="remove(u)">
          <FeatherIcon name="x" class="h-3 w-3" />
        </button>
      </li>
    </ul>
    <UserPicker
      v-if="modelValue.length < limit"
      :users="users"
      :exclude="modelValue"
      placeholder="Add an HR assessor by name or email"
      @select="add"
    />
    <p class="text-xs text-gray-500">They are added to the meeting, emailed the details, and can open the candidate's CV and SOP and score the HR sheet on Interview Panel.</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import UserPicker from '@/components/common/UserPicker.vue'
import { interviewService } from '@/services/interviews'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  limit: { type: Number, default: 2 },
  // [{ assessor, assessor_name }] already on the interview, for their names
  known: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const users = ref([])
onMounted(async () => {
  try {
    users.value = await interviewService.getPanelOptions()
  } catch {
    users.value = []
  }
})

function nameOf(user) {
  return users.value.find((u) => u.name === user)?.full_name || props.known.find((k) => k.assessor === user)?.assessor_name || user
}
function add(u) {
  if (props.modelValue.length >= props.limit || props.modelValue.includes(u.name)) return
  emit('update:modelValue', [...props.modelValue, u.name])
}
function remove(user) {
  emit('update:modelValue', props.modelValue.filter((u) => u !== user))
}
</script>
