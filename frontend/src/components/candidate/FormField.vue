<template>
  <!-- Wraps one apply-form control: outlines it and shows its error below.
       data-field lets the page scroll to the first invalid field. -->
  <div :data-field="name" :class="{ 'field-invalid': !!error }">
    <slot />
    <p v-if="error" class="mt-1 text-xs text-red-600">{{ error }}</p>
  </div>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  error: { type: String, default: '' },
})
</script>
