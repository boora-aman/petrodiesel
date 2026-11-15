<template>
	<div>
		<PageHeader title="Reports" subtitle="Sales, stock, credit and compliance" />
		<div v-for="g in groups" :key="g" class="mb-6">
			<h2 class="mb-2 text-[12px] font-semibold uppercase tracking-wider text-ink-3">
				{{ g }}
			</h2>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
				<RouterLink
					v-for="r in REPORTS.filter((x) => x.group === g)"
					:key="r.name"
					:to="`/reports/${encodeURIComponent(r.name)}`"
					class="card card-pad flex gap-3 hover:border-brand-600"
				>
					<span
						class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-brand-50"
						><i :class="r.icon" class="size-5 text-brand-600"
					/></span>
					<span
						><span class="block text-[14px] font-semibold">{{ r.name }}</span
						><span class="block text-[12px] text-ink-2">{{ r.desc }}</span></span
					>
				</RouterLink>
			</div>
		</div>
	</div>
</template>
<script setup>
import { REPORTS } from "../reports";
import PageHeader from "../components/PageHeader.vue";
const groups = [...new Set(REPORTS.map((r) => r.group))];
</script>
