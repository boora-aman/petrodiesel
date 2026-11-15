<template>
	<div class="card card-pad" :class="tank.reorder ? '!border-red-200 bg-red-50/30' : ''">
		<div class="flex items-center justify-between gap-2">
			<div class="flex items-center gap-2">
				<FuelChip :item="tank.fuel_item" /><span class="text-[14px] font-semibold">{{
					tank.name
				}}</span>
			</div>
			<span class="text-[11px] text-ink-3">Cap {{ litres(tank.capacity_liters, 0) }}</span>
		</div>
		<div class="mt-3 flex items-end justify-between">
			<span class="num text-[22px] font-semibold">{{ litres(tank.book_stock, 0) }}</span>
			<span class="num text-[13px] font-semibold" :style="{ color }">{{ tank.fill }}%</span>
		</div>
		<div class="mt-2 h-3 overflow-hidden rounded-full bg-slate-100">
			<div
				class="h-full rounded-full transition-all"
				:style="{ width: Math.min(tank.fill, 100) + '%', background: color }"
			/>
		</div>
		<div class="mt-2 flex justify-between text-[11px] text-ink-2">
			<span>Space: {{ litres(Math.max(tank.ullage, 0), 0) }}</span>
			<span :class="tank.reorder ? 'font-semibold text-red-600' : ''"
				>Cover: {{ tank.days_cover ?? "—" }} days</span
			>
		</div>
		<div
			v-if="tank.reorder"
			class="mt-2 rounded-md bg-red-100 px-2 py-1 text-[11px] font-semibold text-red-700"
		>
			Order now — under 2 days cover
		</div>
		<div class="mt-2 border-t border-line pt-2 text-[11px] text-ink-3">
			Last dip {{ tank.last_dip_mm ? num(tank.last_dip_mm, 0) + " mm" : "—" }} ·
			{{ dateTimeFmt(tank.last_dip_on) }}
		</div>
	</div>
</template>
<script setup>
import { computed } from "vue";
import FuelChip from "./FuelChip.vue";
import { litres, num, dateTimeFmt, fuelClass, FUEL_COLORS } from "../format";
const props = defineProps({ tank: Object });
const color = computed(() => FUEL_COLORS[fuelClass(props.tank.fuel_item)]);
</script>
