<template>
  <div class="relative">
    <input
      ref="inp"
      v-model="text"
      class="inp"
      :class="invalid ? '!border-red-400' : ''"
      :placeholder="placeholder || 'Search…'"
      :disabled="disabled"
      @focus="open"
      @input="onType"
      @blur="onBlur"
      @keydown.down.prevent="move(1)"
      @keydown.up.prevent="move(-1)"
      @keydown.enter.prevent="pick(options[hi])"
    />
    <div v-if="show && options.length" class="absolute left-0 right-0 top-10 z-40 max-h-64 overflow-y-auto rounded-lg border border-line bg-white py-1 shadow-lg">
      <button
        v-for="(o, i) in options"
        :key="o.value"
        type="button"
        class="block w-full px-3 py-1.5 text-left text-[13px]"
        :class="i === hi ? 'bg-brand-50' : 'hover:bg-gray-50'"
        @mousedown.prevent="pick(o)"
      >
        <div class="font-medium">{{ o.value }}</div>
        <div v-if="o.description" class="truncate text-[11px] text-ink-3">{{ o.description }}</div>
      </button>
    </div>
  </div>
</template>
<script setup>
import { ref, watch } from 'vue'
import { searchLink } from '../api'
const props = defineProps({ modelValue: String, doctype: String, filters: Object, placeholder: String, disabled: Boolean,
  invalid: Boolean })
const emit = defineEmits(['update:modelValue', 'change'])
const text = ref(props.modelValue || '')
const options = ref([])
const show = ref(false)
const hi = ref(0)
let timer
watch(() => props.modelValue, (v) => { text.value = v || '' })
async function load() {
  options.value = await searchLink(props.doctype, text.value, props.filters)
  hi.value = 0
}
function open() { show.value = true; load() }
function onType() { show.value = true; clearTimeout(timer); timer = setTimeout(load, 200) }
function move(d) { hi.value = Math.max(0, Math.min(options.value.length - 1, hi.value + d)) }
function pick(o) {
  if (!o) return
  text.value = o.value
  show.value = false
  emit('update:modelValue', o.value)
  emit('change', o.value)
}
function onBlur() {
  setTimeout(() => {
    show.value = false
    if (!text.value && props.modelValue) { emit('update:modelValue', ''); emit('change', '') }
    else if (text.value !== (props.modelValue || '')) text.value = props.modelValue || ''
  }, 150)
}
</script>
