<template>
  <!-- Draw a signature with a mouse, finger or stylus (workflow step 18).
       v-model is the signature as a PNG data URL ('' when empty). -->
  <div class="flex flex-col gap-1.5">
    <div class="relative overflow-hidden rounded-lg border bg-white" :class="disabled ? 'border-gray-200 opacity-70' : 'border-gray-300'">
      <img v-if="modelValue && !drawing && !dirty" :src="modelValue" alt="Saved signature" class="pointer-events-none absolute inset-0 h-full w-full object-contain" />
      <canvas
        ref="canvas"
        class="block w-full touch-none"
        :class="disabled ? 'cursor-not-allowed' : 'cursor-crosshair'"
        :style="{ height: `${height}px` }"
        role="img"
        :aria-label="label"
        @pointerdown="start"
        @pointermove="move"
        @pointerup="end"
        @pointerleave="end"
        @pointercancel="end"
      />
      <span v-if="!modelValue && !dirty" class="pointer-events-none absolute inset-x-0 bottom-3 text-center text-xs text-gray-400">{{ placeholder }}</span>
      <div class="pointer-events-none absolute inset-x-6 bottom-8 border-b border-dashed border-gray-300" />
    </div>
    <div class="flex items-center justify-between text-xs text-gray-500">
      <span>{{ label }}</span>
      <button v-if="!disabled && (modelValue || dirty)" type="button" class="text-brand-700 hover:underline" @click="clear">Clear</button>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: 'Signature' },
  placeholder: { type: String, default: 'Sign here' },
  height: { type: Number, default: 140 },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const canvas = ref(null)
const drawing = ref(false)
const dirty = ref(false)
let ctx = null
let last = null

function setup() {
  const el = canvas.value
  if (!el) return
  const ratio = window.devicePixelRatio || 1
  const rect = el.getBoundingClientRect()
  el.width = Math.max(1, Math.round(rect.width * ratio))
  el.height = Math.max(1, Math.round(rect.height * ratio))
  ctx = el.getContext('2d')
  ctx.scale(ratio, ratio)
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#111827'
  dirty.value = false
}

function point(event) {
  const rect = canvas.value.getBoundingClientRect()
  return { x: event.clientX - rect.left, y: event.clientY - rect.top }
}

function start(event) {
  if (props.disabled || !ctx) return
  canvas.value.setPointerCapture?.(event.pointerId)
  // Drawing again replaces a signature saved earlier.
  if (!dirty.value) ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  drawing.value = true
  dirty.value = true
  last = point(event)
  ctx.beginPath()
  ctx.arc(last.x, last.y, 1, 0, Math.PI * 2)
  ctx.fillStyle = '#111827'
  ctx.fill()
}

function move(event) {
  if (!drawing.value) return
  const p = point(event)
  ctx.beginPath()
  ctx.moveTo(last.x, last.y)
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
  last = p
}

function end() {
  if (!drawing.value) return
  drawing.value = false
  emit('update:modelValue', canvas.value.toDataURL('image/png'))
}

function clear() {
  if (ctx) ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  dirty.value = false
  emit('update:modelValue', '')
}

let observer = null
onMounted(() => {
  setup()
  // Keep the canvas sharp when the layout changes width.
  if (window.ResizeObserver) {
    observer = new ResizeObserver(() => {
      if (!dirty.value) setup()
    })
    observer.observe(canvas.value)
  }
})
onBeforeUnmount(() => observer?.disconnect())

defineExpose({ clear })
</script>
