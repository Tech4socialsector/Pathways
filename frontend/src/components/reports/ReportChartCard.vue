<template>
  <section class="flex min-w-0 flex-col rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5">
    <header class="flex flex-wrap items-start justify-between gap-x-3 gap-y-1">
      <div class="min-w-0 flex-1 basis-48">
        <h2 class="text-base font-semibold text-gray-900">{{ chart.title }}</h2>
        <p class="mt-0.5 text-sm text-gray-500">{{ chart.subtitle }}</p>
      </div>
      <Dropdown v-if="chart.total" :options="menu" placement="right">
        <!-- Visible label: Dropdown blanks the trigger's aria-label. -->
        <Button variant="ghost" size="sm" icon-left="download">Export</Button>
      </Dropdown>
    </header>

    <div v-if="!chart.total" class="flex flex-1 items-center justify-center py-20 text-sm text-gray-500">
      No applications match these filters.
    </div>
    <template v-else>
      <EChart ref="echart" class="mt-3" :build="build" />
      <!-- Legend with counts, so colour never carries identity alone. -->
      <ul v-if="legend.length" class="mt-3 flex flex-wrap justify-center gap-x-5 gap-y-1.5 text-sm">
        <li
          v-for="item in legend"
          :key="item.label"
          class="flex items-center gap-1.5"
          :class="!item.value && 'opacity-50'"
          @mouseenter="item.value && echart?.highlight(target(item))"
          @mouseleave="item.value && echart?.downplay(target(item))"
        >
          <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ backgroundColor: item.color }" aria-hidden="true" />
          <span class="text-gray-800">{{ item.label }}</span>
          <span class="tabular-nums text-gray-500">{{ item.value }} ({{ item.share }})</span>
        </li>
      </ul>
    </template>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Dropdown } from 'frappe-ui'
import EChart from '@/components/reports/EChart.vue'
import { chartOption, downloadChartCsv, downloadChartPng, legendItems } from '@/utils/reportCharts'
import { toast } from '@/utils/notify'

const props = defineProps({
  // One chart from pathways.api.reports.get_report_charts.
  chart: { type: Object, required: true },
})

const echart = ref(null)
// A new function per chart data, so EChart redraws when the filters change.
const build = computed(() => {
  const chart = props.chart
  return (width) => chartOption(chart, { width })
})
const legend = computed(() => legendItems(props.chart))

function target(item) {
  return props.chart.kind === 'stacked' ? { seriesName: item.label } : { seriesIndex: 0, name: item.label }
}

function run(download) {
  try {
    download(props.chart)
  } catch {
    toast({ title: 'Could not create the download.', icon: 'alert-triangle', iconClasses: 'text-red-500' })
  }
}

const menu = [
  { label: 'Download image (PNG)', icon: 'image', onClick: () => run(downloadChartPng) },
  { label: 'Download data (CSV)', icon: 'file-text', onClick: () => run(downloadChartCsv) },
]
</script>
