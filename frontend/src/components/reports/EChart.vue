<template>
  <div ref="el" class="w-full" :style="{ height: `${height}px` }" />
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { echarts } from '@/utils/reportCharts'

const props = defineProps({
  // (width in px) => { option, height }. Called with the element's real
  // width before the first draw, so it is drawn once at the right size.
  build: { type: Function, required: true },
})

const el = ref(null)
const height = ref(0)
let chart = null
let observer = null
let drawnWidth = 0

function draw({ animate }) {
  if (!chart || !el.value) return
  drawnWidth = el.value.clientWidth
  const built = props.build(drawnWidth || 600)
  height.value = built.height
  chart.setOption(animate ? built.option : { ...built.option, animation: false }, true)
  nextTick(() => chart?.resize())
}

onMounted(() => {
  height.value = props.build(el.value.clientWidth || 600).height
  chart = echarts.init(el.value, null, { renderer: 'canvas' })
  draw({ animate: true })
  observer = new ResizeObserver(() => {
    if (!chart || !el.value) return
    // Labels are fitted to the width: rebuild when it changes (no
    // animation, so a resize never shows two layouts at once).
    if (Math.abs(el.value.clientWidth - drawnWidth) >= 8) draw({ animate: false })
    else chart.resize()
  })
  observer.observe(el.value)
})

// New data (filters changed): redraw with the transition.
watch(
  () => props.build,
  () => draw({ animate: true }),
)

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
  chart = null
})

// Legend hover highlights the matching slice (pie) or series (stacked).
defineExpose({
  highlight: (target) => chart?.dispatchAction({ type: 'highlight', ...target }),
  downplay: (target) => chart?.dispatchAction({ type: 'downplay', ...target }),
})
</script>
