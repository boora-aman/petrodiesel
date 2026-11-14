<template>
  <button type="button" class="flex items-center justify-between gap-3 rounded-lg border border-line px-3 py-2.5 text-left text-[13px]"
    :class="modelValue ? 'bg-green-50/60' : 'bg-white'" :disabled="disabled" @click="$emit('update:modelValue', modelValue ? 0 : 1)">
    <span class="font-medium">{{ label }}</span>
    <span class="relative h-5 w-9 shrink-0 rounded-full transition" :class="modelValue ? 'bg-brand-600' : 'bg-slate-300'">
      <span class="absolute top-0.5 size-4 rounded-full bg-white shadow transition-all" :class="modelValue ? 'left-[18px]' : 'left-0.5'" />
    </span>
  </button>
</template>
<script setup>
defineProps({ modelValue: [Number, Boolean], label: String, disabled: Boolean })
defineEmits(['update:modelValue'])
</script>
