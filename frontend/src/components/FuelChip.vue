<template>
  <span class="pill" :class="[cls, size === 'xs' ? '!h-[18px] !px-1.5 !text-[10px]' : '']">{{ label || item }}</span>
</template>
<script setup>
import { computed } from 'vue'
import { fuelClass } from '../format'
const props = defineProps({ item: String, label: String, size: String })
const cls = computed(() => ({
  ms: 'bg-green-100 text-green-700 border-green-300',
  hsd: 'bg-amber-100 text-amber-700 border-amber-300',
  xp: 'bg-purple-100 text-purple-700 border-purple-300',
  lube: 'bg-slate-100 text-slate-700 border-slate-300',
})[fuelClass(props.item)])
</script>
