<template>
  <div>
    <div class="mb-2 flex flex-wrap gap-3">
      <span v-for="(d, i) in datasets" :key="d.name" class="flex items-center gap-1.5 text-[11px] text-ink-2">
        <span class="h-0.5 w-3" :style="{ background: colorOf(d.name, i) }" />{{ d.name }}
      </span>
    </div>
    <svg :viewBox="`0 0 ${W} ${H}`" class="w-full" :style="{ height: height + 'px' }" preserveAspectRatio="none">
      <line x1="0" :x2="W" :y1="y(0)" :y2="y(0)" stroke="#CBD5E1" stroke-dasharray="4 4" vector-effect="non-scaling-stroke" />
      <polyline v-for="(d, i) in datasets" :key="d.name" fill="none" :stroke="colorOf(d.name, i)" stroke-width="2"
        vector-effect="non-scaling-stroke" :points="points(d)" />
    </svg>
    <div class="mt-1 flex justify-between text-[10px] text-ink-3">
      <span>{{ labels[0] }}</span><span>{{ fmtRange }}</span><span>{{ labels[labels.length - 1] }}</span>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { fuelClass, FUEL_COLORS, num } from '../../format'
const props = defineProps({ labels: { type: Array, default: () => [] }, datasets: { type: Array, default: () => [] },
  height: { type: Number, default: 160 }, unit: { type: String, default: '' } })
const W = 600, H = 160
const PALETTE = ['#0F766E', '#2563EB', '#D97706', '#7C3AED']
const colorOf = (name, i) => (fuelClass(name) !== 'lube' ? FUEL_COLORS[fuelClass(name)] : PALETTE[i % 4])
const all = computed(() => props.datasets.flatMap((d) => d.values.map(Number)))
const min = computed(() => Math.min(0, ...all.value))
const max = computed(() => Math.max(0, ...all.value) || 1)
const y = (v) => H - 6 - ((v - min.value) / (max.value - min.value || 1)) * (H - 12)
const points = (d) => d.values.map((v, i) => `${(i / Math.max(d.values.length - 1, 1)) * W},${y(Number(v))}`).join(' ')
const fmtRange = computed(() => `${num(min.value, 1)} … ${num(max.value, 1)} ${props.unit}`)
</script>
