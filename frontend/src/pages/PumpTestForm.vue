<template>
	<div v-if="f.doc.value">
		<PageHeader
			:title="f.isNew.value ? 'New pump test' : d.name"
			back="/pump-tests"
			:subtitle="`${d.test_type} · ${dateFmt(d.posting_date)}`"
		>
			<template #badge><StatusPill :status="f.state.value" /></template>
			<template #actions><FormActions :form="f" /></template>
		</PageHeader>
		<div class="card card-pad mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
			<Field label="Test type"
				><select v-model="d.test_type" class="inp" :disabled="!ed">
					<option v-for="t in types" :key="t">{{ t }}</option>
				</select></Field
			>
			<Field label="Date"
				><input v-model="d.posting_date" type="date" class="inp" :disabled="!ed"
			/></Field>
			<Field label="Tested by"
				><EmployeeSelect v-model="d.tested_by" :disabled="!ed"
			/></Field>
			<Field label="5 L measure certificate"
				><input v-model="d.measure_certificate_no" class="inp" :disabled="!ed"
			/></Field>
		</div>
		<div
			v-if="failed.length"
			class="mb-4 flex gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-red-700"
		>
			<i class="lucide-octagon-alert mt-0.5 size-4" />{{ failed.join(", ") }} outside ±{{
				tol
			}}
			ml.
			{{
				d.docstatus === 1
					? "Nozzle set Under Maintenance."
					: "On submit the nozzle is set Under Maintenance."
			}}
			Stop sales and call the service engineer.
		</div>
		<div
			v-else-if="
				d.tests.length &&
				d.tests.every((r) => r.error_ml !== null && r.error_ml !== undefined)
			"
			class="mb-4 flex gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-[13px] text-green-700"
		>
			<i class="lucide-circle-check size-4" />All nozzles within ±{{ tol }} ml per 5 L.
		</div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
			<div
				v-for="r in d.tests"
				:key="r._key"
				class="card card-pad"
				:class="result(r) === 'Fail' ? '!border-red-300' : ''"
			>
				<div class="mb-2 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<FuelChip :item="r.fuel_item" />{{ r.nozzle }}
					</div>
					<StatusPill :status="result(r)" />
				</div>
				<Field label="Error (ml, + / −)"
					><NumInput v-model="r.error_ml" big :disabled="!ed"
				/></Field>
				<div class="mt-2 flex gap-1">
					<button
						v-for="v in [-15, -10, -5, 0, 5, 10, 15]"
						:key="v"
						class="flex-1 rounded border border-line py-1 text-[11px]"
						:disabled="!ed"
						@click="r.error_ml = v"
					>
						{{ v > 0 ? "+" + v : v }}
					</button>
				</div>
				<label class="mt-2 flex items-center gap-2 text-[12px]"
					><input
						v-model="r.returned_to_tank"
						type="checkbox"
						:true-value="1"
						:false-value="0"
						:disabled="!ed"
					/>Returned to tank</label
				>
			</div>
		</div>
		<Section title="Remarks" class="mt-4">
			<textarea v-model="d.remarks" class="inp h-16 py-2" :disabled="!ed" />
		</Section>
	</div>
</template>
<script setup>
import { computed, onMounted } from "vue";
import { useDocForm, nextKey } from "../composables/useDocForm";
import { getList } from "../api";
import { session } from "../session";
import { dateFmt, today, flt } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
import NumInput from "../components/NumInput.vue";
import LinkInput from "../components/LinkInput.vue";
import FuelChip from "../components/FuelChip.vue";
import EmployeeSelect from "../components/EmployeeSelect.vue";
import StatusPill from "../components/StatusPill.vue";
import FormActions from "../components/FormActions.vue";

const props = defineProps({ name: String });
const types = [
	"Daily Check",
	"Customer Request",
	"W&M Inspection",
	"OMC Inspection",
	"After Repair / Calibration",
];
const f = useDocForm({
	doctype: "Pump Test Log",
	name: props.name,
	route: "/pump-tests",
	tables: ["tests"],
	blank: async () => {
		const nz = await getList("Fuel Nozzle Master", {
			filters: { station: session.station, status: "Active" },
			fields: ["name", "fuel_item"],
			order_by: "name",
		});
		return {
			doctype: "Pump Test Log",
			station: session.station,
			posting_date: today(),
			posting_time: new Date().toTimeString().slice(0, 8),
			test_type: "Daily Check",
			tested_by: session.boot.employee?.name || "",
			tests: nz.map((n) => ({
				nozzle: n.name,
				fuel_item: n.fuel_item,
				measure_liters: 5,
				error_ml: 0,
				returned_to_tank: 1,
				_key: nextKey(),
			})),
		};
	},
});
const d = computed(() => f.doc.value);
const ed = computed(() => f.editable.value);
const tol = computed(() => flt(session.boot.settings?.pump_test_tolerance_ml) || 15);
const result = (r) =>
	r.result && !ed.value
		? r.result
		: Math.abs(flt(r.error_ml)) <= (tol.value * flt(r.measure_liters || 5)) / 5
		? "Pass"
		: "Fail";
const failed = computed(() =>
	d.value.tests.filter((r) => result(r) === "Fail").map((r) => r.nozzle)
);
onMounted(() => f.load());
</script>
