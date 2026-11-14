<template>
  <div class="mb-4 flex flex-wrap items-start gap-3 lg:mb-6">
    <button v-if="back" class="btn-ghost !px-2" @click="goBack"><i class="lucide-arrow-left size-5" /></button>
    <div class="min-w-0 flex-1">
      <div class="flex flex-wrap items-center gap-2">
        <h1 class="h-title">{{ title }}</h1>
        <slot name="badge" />
      </div>
      <p v-if="subtitle" class="mt-0.5 text-[13px] text-ink-2">{{ subtitle }}</p>
    </div>
    <div class="flex w-full flex-wrap items-center gap-2 sm:w-auto"><slot name="actions" /></div>
  </div>
</template>
<script setup>
import { useRouter } from 'vue-router'
const props = defineProps({ title: String, subtitle: String, back: [String, Boolean] })
const router = useRouter()
function goBack() {
  if (window.history.length > 1) router.back()
  else router.push(typeof props.back === 'string' ? props.back : '/')
}
</script>
