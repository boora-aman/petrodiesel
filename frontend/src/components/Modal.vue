<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 sm:items-center sm:p-4" @click.self="close">
      <div class="max-h-[92vh] w-full overflow-y-auto rounded-t-xl border border-line bg-white shadow-xl sm:rounded-xl" :class="width">
        <div class="flex items-center gap-2 border-b border-line px-4 py-3">
          <h3 class="flex-1 text-[15px] font-semibold">{{ title }}</h3>
          <button class="btn-ghost !px-2" @click="close"><i class="lucide-x size-4" /></button>
        </div>
        <div class="p-4"><slot /></div>
        <div v-if="$slots.footer" class="flex justify-end gap-2 border-t border-line px-4 py-3"><slot name="footer" /></div>
      </div>
    </div>
  </Teleport>
</template>
<script setup>
const props = defineProps({ modelValue: Boolean, title: String, width: { type: String, default: 'sm:max-w-md' } })
const emit = defineEmits(['update:modelValue'])
const close = () => emit('update:modelValue', false)
</script>
