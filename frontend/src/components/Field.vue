<template>
	<label class="block">
		<span v-if="label" class="lbl mb-1 flex items-center gap-1"
			>{{ label }}<span v-if="required" class="text-red-500">*</span></span
		>
		<slot />
		<span v-if="hint" class="mt-1 block text-[11px] text-ink-3">{{ hint }}</span>
		<span v-if="error" class="mt-1 block text-[11px] text-red-600">{{ error }}</span>
	</label>
</template>
<script setup>
defineProps({ label: String, required: Boolean, hint: String, error: String });
</script>
