<template>
  <span class="pill" :class="cls"><span class="size-1.5 rounded-full" :class="dot" />{{ label }}</span>
</template>
<script setup>
import { computed } from 'vue'
const props = defineProps({ status: String, tone: String })
const TONE = {
  Draft: 'blue', 'Pending Approval': 'amber', 'Pending Verification': 'amber', Approved: 'green', Accepted: 'green',
  Submitted: 'green', Rejected: 'red', Cancelled: 'gray', Pass: 'green', Fail: 'red', Active: 'green',
  'Under Maintenance': 'amber', Inactive: 'gray', 'Not started': 'gray',
}
const label = computed(() => props.status || '—')
const t = computed(() => props.tone || TONE[props.status] || 'gray')
const cls = computed(() => ({
  green: 'bg-green-50 text-green-700 border-green-200', amber: 'bg-amber-50 text-amber-700 border-amber-200',
  red: 'bg-red-50 text-red-700 border-red-200', blue: 'bg-blue-50 text-blue-700 border-blue-200',
  gray: 'bg-slate-50 text-slate-600 border-slate-200', teal: 'bg-brand-50 text-brand-700 border-brand-100',
})[t.value])
const dot = computed(() => ({ green: 'bg-green-600', amber: 'bg-amber-500', red: 'bg-red-600', blue: 'bg-blue-600',
  gray: 'bg-slate-400', teal: 'bg-brand-600' })[t.value])
</script>
