<template>
  <div class="min-w-0">
    <div v-if="label" class="lbl mb-1 flex items-center justify-between gap-1">
      <span class="truncate">{{ label }}</span>
      <span class="shrink-0 rounded bg-slate-100 px-1 text-[9px] font-semibold uppercase tracking-wider text-slate-400" title="Calculated automatically">auto</span>
    </div>
    <div class="auto" :class="[big ? '!h-11 !text-[18px]' : '', toneClass]" :title="String(value ?? '')">
      <span class="truncate">{{ value }}</span>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ label: String, value: [String, Number], big: Boolean, tone: String })
const toneClass = computed(() => ({ bad: '!text-red-600 !border-red-200 !bg-red-50/50', good: '!text-green-700',
  warn: '!text-amber-700' })[props.tone] || '')
</script>
