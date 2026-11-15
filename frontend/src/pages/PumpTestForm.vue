<template>
	<div v-if="f.doc.value">
		<PageHeader
			:title="f.isNew.value ? 'New pump test' : d.name"
			back="/pump-tests"
			:subtitle="`${d.test_type} · ${dateFmt(d.posting_date)}`"
		>
			<template #badge><StatusPill :status="f.state.value" /></template>
			<template #actions
				><FormActions :form="f" :blocked="!!problem" :blocked-reason="problem"
			/></template>
		</PageHeader>
		<div class="card card-pad mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
			<Field label="Test type"
				><select v-model="d.test_type" class="inp" :disabled="!ed">
					<option v-for="t in types" :key="t">{{ t }}</option>
				</select></Field
			>
			<Field label="Date"
				><input
					v-model="d.posting_date"
					type="date"
					class="inp"
					:max="today()"
					:disabled="!ed"
			/></Field>
			<Field label="Tested by"
				><EmployeeSelect v-model="d.tested_by" :disabled="!ed"
			/></Field>
			<Field label="5 L measure certificate"
				><input v-model="d.measure_certificate_no" class="inp" :disabled="!ed"
			/></Field>
		</div>
		<div
			v-if="ed && pending.length"
			class="mb-4 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] text-amber-800"
		>
			<i class="lucide-info mt-0.5 size-4 shrink-0" />Enter the error (ml) for
			{{ pending.join(", ") }}, or remove nozzles that were not tested.
		</div>
		<div
			v-if="failed.length && !pending.length"
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
			v-else-if="d.tests.length && !pending.length"
			class="mb-4 flex gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-[13px] text-green-700"
		>
			<i class="lucide-circle-check size-4" />All nozzles within ±{{ tol }} ml per 5 L.
		</div>
		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
			<div
				v-for="r in d.tests"
				:key="r._key"
				class="card card-pad"
				:class="result(r) === 'Fail' ? '!border-red-300' : ''"
			>
				<div class="mb-2 flex items-center justify-between">
					<div class="flex items-center gap-2 whitespace-nowrap font-semibold">
						<FuelChip :item="r.fuel_item" />{{ r.nozzle }}
					</div>
					<div class="flex shrink-0 items-center gap-2 whitespace-nowrap">
						<StatusPill v-if="hasValue(r)" :status="result(r)" />
						<span v-else class="text-[12px] text-ink-3">not entered</span>
						<button
							v-if="ed && d.tests.length > 1"
							class="text-ink-3 hover:text-red-600"
							title="Remove: nozzle not tested"
							@click="removeRow(r)"
						>
							<i class="lucide-x size-4" />
						</button>
					</div>
				</div>
				<Field label="Error (ml, + / −)"
					><input
						:value="hasValue(r) ? r.error_ml : ''"
						type="text"
						inputmode="decimal"
						class="inp inp-lg num text-right"
						:class="ed && !hasValue(r) ? '!border-amber-300' : ''"
						placeholder="ml"
						:disabled="!ed"
						@input="onError(r, $event)"
						@focus="$event.target.select()"
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
		<div
			v-if="ed && removed.length"
			class="mt-3 flex flex-wrap items-center gap-2 text-[12px]"
		>
			<span class="text-ink-3">Not tested:</span>
			<button
				v-for="r in removed"
				:key="r._key"
				class="pill border-line hover:bg-gray-50"
				title="Add back"
				@click="restoreRow(r)"
			>
				<i class="lucide-plus size-3" />{{ r.nozzle }}
			</button>
		</div>
		<Section title="Remarks" class="mt-4">
			<textarea v-model="d.remarks" class="inp h-16 py-2" :disabled="!ed" />
		</Section>
	</div>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
import { toast } from "frappe-ui";
import { useDocForm, nextKey } from "../composables/useDocForm";
import { getList } from "../api";
import { session } from "../session";
import { dateFmt, today, flt } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
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
				error_ml: null,
				returned_to_tank: 1,
				_key: nextKey(),
			})),
		};
	},
});
const d = computed(() => f.doc.value);
const ed = computed(() => f.editable.value);
const tol = computed(() => flt(session.boot.settings?.pump_test_tolerance_ml) || 15);
const removed = ref([]);
const hasValue = (r) => r.error_ml !== null && r.error_ml !== undefined && r.error_ml !== "";
function onError(r, e) {
	const raw = e.target.value.replace(/[^0-9.\-]/g, "");
	if (raw !== e.target.value) e.target.value = raw;
	r.error_ml =
		raw === "" || raw === "-" || raw === "." || isNaN(Number(raw)) ? null : Number(raw);
}
function removeRow(r) {
	d.value.tests.splice(d.value.tests.indexOf(r), 1);
	removed.value.push(r);
}
function restoreRow(r) {
	removed.value.splice(removed.value.indexOf(r), 1);
	d.value.tests.push(r);
}
const pending = computed(() => d.value.tests.filter((r) => !hasValue(r)).map((r) => r.nozzle));
const problem = computed(() => {
	if (!d.value.tests.length) return "Add at least one nozzle test";
	if (d.value.posting_date > today()) return "Date cannot be in the future";
	if (pending.value.length) return "Enter the error (ml) for " + pending.value.join(", ");
	return "";
});
// the server rejects drafts with a missing error too: say so before calling it
const serverSave = f.save;
f.save = (action) => {
	if (problem.value) {
		toast.error(problem.value);
		return;
	}
	return serverSave(action);
};
const result = (r) =>
	r.result && !ed.value
		? r.result
		: Math.abs(flt(r.error_ml)) <= (tol.value * flt(r.measure_liters || 5)) / 5
		? "Pass"
		: "Fail";
const failed = computed(() =>
	d.value.tests.filter((r) => hasValue(r) && result(r) === "Fail").map((r) => r.nozzle)
);
onMounted(() => f.load());
</script>
