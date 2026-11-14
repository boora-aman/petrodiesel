<template>
  <div class="flex flex-col items-center justify-center gap-2 py-12 text-center">
    <div class="flex size-12 items-center justify-center rounded-full bg-slate-100"><i :class="icon" class="size-6 text-ink-3" /></div>
    <div class="text-[14px] font-medium">{{ title }}</div>
    <div v-if="text" class="max-w-sm text-[13px] text-ink-2">{{ text }}</div>
    <slot />
  </div>
</template>
<script setup>
defineProps({ title: String, text: String, icon: { type: String, default: 'lucide-inbox' } })
</script>
