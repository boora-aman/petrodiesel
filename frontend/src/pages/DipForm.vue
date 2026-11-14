<template>
	<div v-if="f.doc.value">
		<PageHeader
			:title="f.isNew.value ? 'New dip reading' : d.name"
			back="/dips"
			:subtitle="`${d.reading_type} · ${dateFmt(d.posting_date)} ${timeFmt(d.posting_time)}`"
		>
			<template #badge><StatusPill :status="f.state.value" /></template>
			<template #actions><FormActions :form="f" /></template>
		</PageHeader>
		<div
			v-if="f.serverError.value && ed"
			class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] text-amber-800"
		>
			{{ f.serverError.value }}
		</div>

		<div class="card card-pad mb-4 space-y-3">
			<div class="flex flex-wrap gap-1.5">
				<button
					v-for="t in types"
					:key="t"
					class="rounded-full border px-3 py-1.5 text-[12px] font-medium"
					:class="
						d.reading_type === t
							? 'border-brand-600 bg-brand-600 text-white'
							: 'border-line bg-white text-ink-2'
					"
					:disabled="!ed"
					@click="d.reading_type = t"
				>
					{{ t }}
				</button>
			</div>
			<div class="grid grid-cols-2 gap-3 md:grid-cols-4">
				<Field label="Date"
					><input
						v-model="d.posting_date"
						type="date"
						class="inp"
						:disabled="!ed"
						@change="calc"
				/></Field>
				<Field label="Time"
					><input
						v-model="d.posting_time"
						type="time"
						step="1"
						class="inp"
						:disabled="!ed"
						@change="calc"
				/></Field>
				<Field label="Recorded by"
					><EmployeeSelect v-model="d.recorded_by" :disabled="!ed"
				/></Field>
				<div class="flex items-end">
					<button v-if="ed" class="btn-secondary w-full" @click="loadTanks">
						<i class="lucide-download size-4" />Load tanks
					</button>
				</div>
			</div>
		</div>

		<div
			v-for="r in d.readings.filter((x) => x.water_dip_mm > 0)"
			:key="'w' + r._key"
			class="mb-3 flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-[13px] text-blue-800"
		>
			<i class="lucide-droplets size-4" />Water found in {{ r.tank }} ({{ r.water_dip_mm }}
			mm). Inform the OMC and arrange removal.
		</div>

		<EmptyState
			v-if="!d.readings.length"
			title="No tanks loaded"
			text="Tap “Load tanks”."
			icon="lucide-ruler"
		/>
		<div class="grid grid-cols-1 gap-3 md:grid-cols-2">
			<div v-for="r in d.readings" :key="r._key" class="card card-pad">
				<div class="mb-3 flex items-center gap-2">
					<FuelChip :item="r.fuel_item" /><span class="text-[15px] font-semibold">{{
						r.tank
					}}</span>
				</div>
				<div class="flex gap-4">
					<TankSection :fill="fillPct(r)" :water="waterPct(r)" :color="color(r)" />
					<div class="grid flex-1 grid-cols-2 gap-3">
						<Field label="Product dip (mm)" class="col-span-2"
							><NumInput
								v-model="r.dip_mm"
								big
								:disabled="!ed"
								@update:model-value="calc"
						/></Field>
						<Field label="Water dip (mm)"
							><NumInput
								v-model="r.water_dip_mm"
								:disabled="!ed"
								@update:model-value="calc"
						/></Field>
						<Field label="Temp °C"
							><NumInput v-model="r.temperature" :disabled="!ed"
						/></Field>
						<Field label="Observed density"
							><NumInput v-model="r.observed_density" :disabled="!ed"
						/></Field>
						<Field label="Density @15°C"
							><NumInput v-model="r.density_at_15" :disabled="!ed"
						/></Field>
					</div>
				</div>
				<div class="mt-3 grid grid-cols-3 gap-2">
					<AutoField label="Dip stock (L)" :value="num(r.dip_stock)" />
					<AutoField label="Book stock (L)" :value="num(r.book_stock)" />
					<AutoField
						label="Variance (L)"
						:value="num(r.variance)"
						:tone="r.variance < -0.5 ? 'bad' : 'good'"
					/>
				</div>
			</div>
		</div>

		<div v-if="d.readings.length" class="card card-pad mt-4 grid grid-cols-3 gap-3">
			<AutoField label="Total dip stock" :value="litres(d.total_dip_stock)" />
			<AutoField label="Total book stock" :value="litres(d.total_book_stock)" />
			<AutoField
				label="Total variance"
				:value="litres(d.total_variance)"
				:tone="d.total_variance < -0.5 ? 'bad' : 'good'"
			/>
		</div>
		<Section title="Remarks" class="mt-4">
			<textarea v-model="d.remarks" class="inp h-16 py-2" :disabled="!ed" />
		</Section>
	</div>
</template>
<script setup>
import { computed, onMounted, ref, h } from "vue";
import { useDocForm, nextKey } from "../composables/useDocForm";
import { api, getList } from "../api";
import { session } from "../session";
import { num, litres, dateFmt, timeFmt, today, flt, fuelClass, FUEL_COLORS } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
import AutoField from "../components/AutoField.vue";
import NumInput from "../components/NumInput.vue";
import LinkInput from "../components/LinkInput.vue";
import FuelChip from "../components/FuelChip.vue";
import EmployeeSelect from "../components/EmployeeSelect.vue";
import StatusPill from "../components/StatusPill.vue";
import EmptyState from "../components/EmptyState.vue";
import FormActions from "../components/FormActions.vue";

const TankSection = (p) =>
	h(
		"div",
		{
			class: "relative h-32 w-16 shrink-0 overflow-hidden rounded-[18px] border-2 border-slate-300 bg-slate-50",
		},
		[
			h("div", {
				class: "absolute inset-x-0 bottom-0 transition-all",
				style: { height: p.fill + "%", background: p.color, opacity: 0.75 },
			}),
			h("div", {
				class: "absolute inset-x-0 bottom-0 bg-blue-500",
				style: { height: p.water + "%" },
			}),
		]
	);
TankSection.props = ["fill", "water", "color"];

const props = defineProps({ name: String });
const caps = ref({});
const types = [
	"Morning (Opening)",
	"Night (Closing)",
	"Shift Change",
	"Before Decantation",
	"After Decantation",
	"Surprise Check",
];
const guessType = () => {
	const hr = new Date().getHours();
	return hr < 12 ? "Morning (Opening)" : hr >= 21 ? "Night (Closing)" : "Shift Change";
};
const f = useDocForm({
	doctype: "Tank Dip Reading",
	name: props.name,
	route: "/dips",
	tables: ["readings"],
	blank: () => ({
		doctype: "Tank Dip Reading",
		station: session.station,
		posting_date: today(),
		posting_time: new Date().toTimeString().slice(0, 8),
		reading_type: guessType(),
		recorded_by: session.boot.employee?.name || "",
		readings: [],
	}),
});
const d = computed(() => f.doc.value);
const ed = computed(() => f.editable.value);
const color = (r) => FUEL_COLORS[fuelClass(r.fuel_item)];
const fillPct = (r) => Math.min(100, (flt(r.dip_stock) * 100) / (caps.value[r.tank] || 1));
const waterPct = (r) => Math.min(100, (flt(r.water_volume) * 100) / (caps.value[r.tank] || 1));

async function loadTanks() {
	const rows = await api(
		"petrodiesel.petrodiesel.doctype.tank_dip_reading.tank_dip_reading.get_tanks",
		{ station: d.value.station }
	);
	d.value.readings = rows.map((r) => ({ ...r, dip_mm: 0, water_dip_mm: 0, _key: nextKey() }));
	calc();
}
function calc() {
	if (!ed.value || !d.value.readings.length) return;
	f.schedule((sd) => {
		sd.readings.forEach((s, i) => {
			const r = d.value.readings[i];
			if (r)
				Object.assign(r, {
					dip_stock: s.dip_stock,
					water_volume: s.water_volume,
					book_stock: s.book_stock,
					variance: s.variance,
					fuel_item: s.fuel_item,
				});
		});
		for (const k of ["total_dip_stock", "total_book_stock", "total_variance"])
			d.value[k] = sd[k];
	}, 400);
}
onMounted(async () => {
	const t = await getList("Fuel Tank Master", {
		filters: { station: session.station },
		fields: ["name", "capacity_liters"],
	});
	caps.value = Object.fromEntries(t.map((x) => [x.name, x.capacity_liters]));
	await f.load();
	if (f.isNew.value) loadTanks();
});
</script>
