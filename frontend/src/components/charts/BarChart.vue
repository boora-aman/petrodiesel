<template>
  <div>
    <div class="mb-2 flex flex-wrap gap-3">
      <span v-for="(d, i) in datasets" :key="d.name" class="flex items-center gap-1.5 text-[11px] text-ink-2">
        <span class="size-2.5 rounded-sm" :style="{ background: colorOf(d.name, i) }" />{{ d.name }}
      </span>
    </div>
    <svg :viewBox="`0 0 ${W} ${H}`" class="w-full" :style="{ height: height + 'px' }" preserveAspectRatio="none">
      <g v-for="t in ticks" :key="t">
        <line :x1="0" :x2="W" :y1="y(t)" :y2="y(t)" stroke="#F1F5F9" vector-effect="non-scaling-stroke" />
      </g>
      <g v-for="(lbl, i) in labels" :key="i">
        <template v-for="(seg, j) in stack(i)" :key="j">
          <rect :x="i * bw + bw * 0.15" :width="bw * 0.7" :y="y(seg.top)" :height="Math.max(y(seg.bottom) - y(seg.top), 0)"
            :fill="seg.color"><title>{{ lbl }} · {{ seg.name }}: {{ fmt(seg.value) }}</title></rect>
        </template>
      </g>
    </svg>
    <div class="mt-1 flex justify-between text-[10px] text-ink-3">
      <span>{{ labels[0] }}</span><span>{{ labels[Math.floor(labels.length / 2)] }}</span><span>{{ labels[labels.length - 1] }}</span>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { fuelClass, FUEL_COLORS, num } from '../../format'
const props = defineProps({ labels: { type: Array, default: () => [] }, datasets: { type: Array, default: () => [] },
  height: { type: Number, default: 200 }, unit: { type: String, default: 'L' } })
const W = 600, H = 200
const PALETTE = ['#0F766E', '#2563EB', '#D97706', '#7C3AED', '#64748B']
const colorOf = (name, i) => (fuelClass(name) !== 'lube' ? FUEL_COLORS[fuelClass(name)] : PALETTE[i % PALETTE.length])
const bw = computed(() => W / Math.max(props.labels.length, 1))
const max = computed(() => {
  let m = 1
  props.labels.forEach((_, i) => { m = Math.max(m, props.datasets.reduce((a, d) => a + Math.max(Number(d.values[i]) || 0, 0), 0)) })
  return m * 1.08
})
const ticks = computed(() => [0.25, 0.5, 0.75, 1].map((f) => max.value * f))
const y = (v) => H - (v / max.value) * H
const fmt = (v) => `${num(v, 0)} ${props.unit}`
function stack(i) {
  let acc = 0
  return props.datasets.map((d, j) => {
    const v = Math.max(Number(d.values[i]) || 0, 0)
    const seg = { bottom: acc, top: acc + v, color: colorOf(d.name, j), name: d.name, value: v }
    acc += v
    return seg
  })
}
</script>
