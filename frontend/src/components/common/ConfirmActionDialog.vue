<template>
  <!-- Asks "are you sure?" before an action; runs `run` on confirm. -->
  <Dialog :model-value="open" :options="{ title, size: 'sm' }" @update:model-value="(v) => emit('update:open', v)">
    <template #body-content>
      <p class="text-sm text-gray-700">{{ message }}</p>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button variant="ghost" @click="emit('update:open', false)">Cancel</Button>
        <Button variant="solid" :class="theme === 'red' ? '' : BTN_BRAND" :theme="theme" :loading="busy" @click="confirm">{{ label || 'Confirm' }}</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from 'vue'
import { Button, Dialog } from 'frappe-ui'
import { BTN_BRAND } from '@/utils/buttonStyles'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: 'Are you sure?' },
  message: { type: String, default: '' },
  label: { type: String, default: '' },
  theme: { type: String, default: 'gray' },
  run: { type: Function, default: null },
})
const emit = defineEmits(['update:open'])
const busy = ref(false)

async function confirm() {
  busy.value = true
  try {
    await props.run?.()
  } finally {
    busy.value = false
    emit('update:open', false)
  }
}
</script>
