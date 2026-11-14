<template>
  <svg :viewBox="`0 0 ${w} ${h}`" class="h-7 w-full" preserveAspectRatio="none">
    <polyline :points="pts" fill="none" :stroke="color" stroke-width="1.6" vector-effect="non-scaling-stroke" />
  </svg>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ values: Array, color: { type: String, default: '#0F766E' } })
const w = 100, h = 28
const pts = computed(() => {
  const v = props.values.map(Number)
  const min = Math.min(...v), max = Math.max(...v), rng = max - min || 1
  return v.map((x, i) => `${(i / (v.length - 1)) * w},${h - 2 - ((x - min) / rng) * (h - 4)}`).join(' ')
})
</script>
