<template>
	<div class="flex flex-col items-center gap-4 sm:flex-row">
		<svg viewBox="0 0 120 120" class="size-40 shrink-0 -rotate-90">
			<circle cx="60" cy="60" r="46" fill="none" stroke="#F1F5F9" stroke-width="16" />
			<circle
				v-for="(s, i) in segs"
				:key="i"
				cx="60"
				cy="60"
				r="46"
				fill="none"
				:stroke="s.color"
				stroke-width="16"
				:stroke-dasharray="`${s.len} ${C - s.len}`"
				:stroke-dashoffset="-s.off"
			>
				<title>{{ s.label }}</title>
			</circle>
		</svg>
		<div class="w-full space-y-1.5">
			<div v-for="s in segs" :key="s.label" class="flex items-center gap-2 text-[12px]">
				<span class="size-2.5 rounded-sm" :style="{ background: s.color }" />
				<span class="flex-1 text-ink-2">{{ s.label }}</span>
				<span class="num text-ink-3">{{ s.pct }}%</span>
				<span class="num w-28 text-right font-medium">{{ inr(s.value, true) }}</span>
			</div>
		</div>
	</div>
</template>
<script setup>
import { computed } from "vue";
import { inr } from "../../format";
const props = defineProps({ labels: Array, values: Array });
const C = 2 * Math.PI * 46;
const COLORS = ["#0F766E", "#D97706", "#2563EB", "#7C3AED", "#DB2777", "#64748B"];
const segs = computed(() => {
	const tot = (props.values || []).reduce((a, v) => a + Math.max(Number(v) || 0, 0), 0) || 1;
	let off = 0;
	return (props.labels || []).map((l, i) => {
		const v = Math.max(Number(props.values[i]) || 0, 0);
		const s = {
			label: l,
			value: v,
			pct: Math.round((v * 100) / tot),
			color: COLORS[i % COLORS.length],
			len: (v / tot) * C,
			off,
		};
		off += s.len;
		return s;
	});
});
</script>
