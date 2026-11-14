<template>
  <div class="card card-pad flex min-w-[170px] flex-col gap-1">
    <div class="flex items-start justify-between gap-2">
      <span class="text-[12px] text-ink-2">{{ label }}</span>
      <span v-if="badge" class="rounded px-1.5 py-0.5 text-[10px] font-semibold" :class="badgeClass">{{ badge }}</span>
    </div>
    <div class="num text-[22px] font-semibold leading-8 tracking-tight" :class="valueClass">
      <Skeleton v-if="loading" class="h-7 w-28" />
      <template v-else>{{ value }}</template>
    </div>
    <div v-if="caption" class="truncate text-[11px] text-ink-3">{{ caption }}</div>
    <Sparkline v-if="spark && spark.length > 1" :values="spark" :color="sparkColor" class="mt-1" />
  </div>
</template>
<script setup>
import { computed } from 'vue'
import Sparkline from './charts/Sparkline.vue'
import Skeleton from './Skeleton.vue'
const props = defineProps({ label: String, value: [String, Number], caption: String, badge: String,
  tone: { type: String, default: 'neutral' }, spark: Array, loading: Boolean })
const badgeClass = computed(() => ({ good: 'bg-green-50 text-green-700', bad: 'bg-red-50 text-red-700',
  warn: 'bg-amber-50 text-amber-700', neutral: 'bg-slate-100 text-slate-600' })[props.tone])
const valueClass = computed(() => (props.tone === 'bad' ? 'text-red-600' : 'text-ink'))
const sparkColor = computed(() => (props.tone === 'bad' ? '#DC2626' : '#0F766E'))
</script>
