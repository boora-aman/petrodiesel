<template>
	<section class="card">
		<div
			v-if="title || $slots.actions"
			class="flex flex-wrap items-center gap-2 border-b border-line px-4 py-3"
		>
			<span
				v-if="step"
				class="flex size-6 items-center justify-center rounded-full bg-brand-600 text-[12px] font-semibold text-white"
				>{{ step }}</span
			>
			<div class="min-w-0 flex-1">
				<h2 class="h-section">{{ title }}</h2>
				<p v-if="subtitle" class="text-[12px] text-ink-3">{{ subtitle }}</p>
			</div>
			<slot name="actions" />
		</div>
		<div :class="flush ? '' : 'p-4'"><slot /></div>
	</section>
</template>
<script setup>
defineProps({ title: String, subtitle: String, step: [String, Number], flush: Boolean });
</script>
