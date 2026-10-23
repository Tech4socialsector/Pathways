<template>
  <div class="flex flex-col gap-3">
    <template v-for="(row, idx) in responses" :key="row.name || idx">
      <div
        v-if="row.section && row.section !== responses[idx - 1]?.section"
        class="mt-1 text-xs font-semibold uppercase tracking-wide text-brand-700"
      >
        {{ row.section }}
      </div>
      <div>
        <div class="text-sm font-medium text-gray-900">{{ idx + 1 }}. {{ row.question_text }}</div>
        <div class="mt-1 whitespace-pre-wrap text-sm text-gray-700">
          <template v-if="row.answer_type === 'Rating 1-5'">
            <span v-if="row.rating_value" class="font-semibold">{{ row.rating_value }} / 5 · {{ RATING_LABELS[row.rating_value] }}</span>
            <span v-else class="text-gray-400">Not rated</span>
            <span v-if="row.answer_text" class="block">{{ row.answer_text }}</span>
          </template>
          <template v-else>
            <span v-if="row.answer_text">{{ row.answer_text }}</span>
            <span v-else class="text-gray-400">No answer</span>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { RATING_LABELS } from '@/components/references/ratings'

defineProps({ responses: { type: Array, default: () => [] } })
</script>
