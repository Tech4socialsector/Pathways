<template>
  <div class="flex flex-col gap-5">
    <template v-for="(q, idx) in questions" :key="q.name">
      <h3
        v-if="q.section && q.section !== questions[idx - 1]?.section"
        class="border-b border-gray-100 pb-1 text-sm font-semibold uppercase tracking-wide text-brand-700"
      >
        {{ q.section }}
      </h3>
      <fieldset class="min-w-0">
        <legend class="mb-1.5 text-sm font-medium text-gray-900">
          {{ idx + 1 }}. {{ q.question }}<span v-if="q.required" class="text-red-600" aria-label="required"> *</span>
        </legend>

        <div v-if="q.answer_type === 'Rating 1-5'" class="flex flex-wrap gap-2" role="radiogroup">
          <button
            v-for="n in 5"
            :key="n"
            type="button"
            role="radio"
            :aria-checked="value(q).rating_value === n"
            class="flex min-w-[4.5rem] flex-col items-center rounded-lg border px-3 py-1.5 text-sm transition"
            :class="value(q).rating_value === n ? 'border-brand-700 bg-brand-700 text-white' : 'border-gray-300 bg-white text-gray-700 hover:border-brand-400'"
            :disabled="disabled"
            @click="set(q, 'rating_value', value(q).rating_value === n ? null : n)"
          >
            <span class="font-bold">{{ n }}</span>
            <span class="text-[11px] leading-tight">{{ RATING_LABELS[n] }}</span>
          </button>
        </div>

        <div v-else-if="q.answer_type === 'Yes-No'" class="flex gap-2" role="radiogroup">
          <button
            v-for="opt in ['Yes', 'No']"
            :key="opt"
            type="button"
            role="radio"
            :aria-checked="value(q).answer_text === opt"
            class="rounded-lg border px-4 py-1.5 text-sm font-medium transition"
            :class="value(q).answer_text === opt ? 'border-brand-700 bg-brand-700 text-white' : 'border-gray-300 bg-white text-gray-700 hover:border-brand-400'"
            :disabled="disabled"
            @click="set(q, 'answer_text', value(q).answer_text === opt ? '' : opt)"
          >
            {{ opt }}
          </button>
        </div>

        <textarea
          v-else
          :value="value(q).answer_text"
          rows="3"
          maxlength="10000"
          :disabled="disabled"
          class="block w-full rounded-md border-gray-300 text-sm shadow-sm focus:border-brand-500 focus:ring-brand-500"
          @input="set(q, 'answer_text', $event.target.value)"
        />
      </fieldset>
    </template>
  </div>
</template>

<script setup>
import { RATING_LABELS } from '@/components/references/ratings'

// modelValue: { [question row name]: { answer_text, rating_value } }
const props = defineProps({
  questions: { type: Array, default: () => [] },
  modelValue: { type: Object, default: () => ({}) },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

function value(q) {
  return props.modelValue[q.name] || {}
}

function set(q, key, val) {
  emit('update:modelValue', { ...props.modelValue, [q.name]: { ...value(q), [key]: val } })
}
</script>
