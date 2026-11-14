<template>
	<div v-if="f.doc.value">
		<PageHeader
			:title="f.isNew.value ? 'Daily stock register' : d.name"
			back="/dsr"
			:subtitle="`${session.boot.station?.station_name} · ${dateFmt(d.posting_date)}`"
		>
			<template #badge><StatusPill :status="f.state.value" /></template>
			<template #actions>
				<FormActions
					:form="f"
					:print-url="
						!f.isNew.value
							? printUrl(
									'Daily Stock Register',
									d.name,
									'Daily Stock Register Print'
							  )
							: ''
					"
					:blocked="missingDips.length > 0"
					:blocked-reason="'Enter closing dips: ' + missingDips.join(', ')"
				/>
			</template>
		</PageHeader>
		<div
			v-if="f.serverError.value && ed"
			class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] text-amber-800"
		>
			{{ f.serverError.value }}
		</div>

		<div class="card card-pad mb-4 flex flex-wrap items-end gap-3">
			<Field label="Business date"
				><input v-model="d.posting_date" type="date" class="inp w-44" :disabled="!ed"
			/></Field>
			<button v-if="ed" class="btn-primary" :disabled="fetching" @click="fetchData">
				<i class="lucide-refresh-cw size-4" :class="fetching ? 'animate-spin' : ''" />Fetch
				day's data
			</button>
			<span
				v-if="missingDips.length && d.items.length"
				class="pill ml-auto border-amber-200 bg-amber-50 text-amber-700"
				>Waiting for closing dips</span
			>
			<span
				v-else
				class="pill ml-auto"
				:class="
					d.all_within_limit
						? 'border-green-200 bg-green-50 text-green-700'
						: 'border-red-200 bg-red-50 text-red-700'
				"
			>
				{{
					d.items.length
						? d.all_within_limit
							? "All tanks within permissible loss"
							: "Loss beyond limit: " + beyond.join(", ")
						: "No data"
				}}
			</span>
		</div>
		<div
			v-if="missingDips.length && ed"
			class="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] text-amber-800"
		>
			No night dip recorded for {{ missingDips.join(", ") }}. Enter the closing dip (mm)
			below, or record a Night (Closing) dip reading and fetch again.
		</div>

		<div class="card hidden overflow-x-auto md:block">
			<table class="tbl">
				<thead>
					<tr>
						<th>Tank</th>
						<th class="!text-right">Opening</th>
						<th class="!text-right">Receipts</th>
						<th class="!text-right">Meter sales</th>
						<th class="!text-right">Testing</th>
						<th class="!text-right">Net sales</th>
						<th class="!text-right">Book closing</th>
						<th class="!text-right">Closing dip mm</th>
						<th class="!text-right">Closing stock</th>
						<th class="!text-right">Gain/Loss</th>
						<th class="!text-right">% sales</th>
						<th class="!text-right">Allowed %</th>
						<th>Check</th>
						<th class="!text-right">MTD</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="r in d.items" :key="r._key">
						<td>
							<div class="flex items-center gap-1.5">
								<FuelChip :item="r.fuel_item" size="xs" />{{ r.tank }}
							</div>
						</td>
						<td class="r">{{ num(r.opening_stock) }}</td>
						<td class="r">{{ num(r.receipts) }}</td>
						<td class="r">{{ num(r.meter_sales) }}</td>
						<td class="r">{{ num(r.test_qty) }}</td>
						<td class="r">{{ num(r.net_sales) }}</td>
						<td class="r font-semibold">{{ num(r.book_closing) }}</td>
						<td class="r w-28">
							<NumInput
								v-if="ed"
								v-model="r.closing_dip_mm"
								class="!h-8"
								@update:model-value="onDip(r)"
							/><span v-else>{{ num(r.closing_dip_mm, 1) }}</span>
						</td>
						<td class="r font-semibold">{{ num(r.closing_stock) }}</td>
						<td
							class="r font-semibold"
							:class="r.variance < 0 ? 'text-red-600' : 'text-green-700'"
						>
							{{ hasClosing(r) ? num(r.variance) : "—" }}
						</td>
						<td class="r">{{ num(r.variance_percent, 3) }}</td>
						<td class="r">{{ num(r.permissible_percent, 2) }}</td>
						<td>
							<StatusPill
								v-if="hasClosing(r)"
								:status="r.within_limit ? 'OK' : 'Beyond'"
								:tone="r.within_limit ? 'green' : 'red'"
							/><span v-else class="text-[12px] text-ink-3">dip pending</span>
						</td>
						<td class="r">{{ num(r.cumulative_variance) }}</td>
					</tr>
				</tbody>
			</table>
		</div>
		<div class="space-y-3 md:hidden">
			<div v-for="r in d.items" :key="r._key" class="card card-pad">
				<div class="mb-2 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<FuelChip :item="r.fuel_item" />{{ r.tank }}
					</div>
					<StatusPill
						:status="r.within_limit ? 'Within limit' : 'Beyond limit'"
						:tone="r.within_limit ? 'green' : 'red'"
					/>
				</div>
				<div class="grid grid-cols-2 gap-2 text-[12px]">
					<div>
						Opening <b class="num">{{ num(r.opening_stock) }}</b>
					</div>
					<div>
						Receipts <b class="num">{{ num(r.receipts) }}</b>
					</div>
					<div>
						Net sales <b class="num">{{ num(r.net_sales) }}</b>
					</div>
					<div>
						Book closing <b class="num">{{ num(r.book_closing) }}</b>
					</div>
				</div>
				<div class="mt-2 grid grid-cols-2 gap-2">
					<Field label="Closing dip (mm)"
						><NumInput
							v-model="r.closing_dip_mm"
							:disabled="!ed"
							@update:model-value="onDip(r)"
					/></Field>
					<AutoField label="Closing stock" :value="num(r.closing_stock)" />
					<AutoField
						label="Gain / loss (L)"
						:value="num(r.variance)"
						:tone="r.variance < 0 ? 'bad' : 'good'"
					/>
					<AutoField
						label="% of sales"
						:value="
							num(r.variance_percent, 3) +
							' (≤ ' +
							num(r.permissible_percent, 2) +
							')'
						"
					/>
				</div>
			</div>
		</div>
		<div class="card card-pad mt-4 grid grid-cols-3 gap-3">
			<AutoField label="Receipts" :value="litres(d.total_receipts)" /><AutoField
				label="Net sales"
				:value="litres(d.total_sales)"
			/>
			<AutoField
				label="Gain / loss"
				:value="missingDips.length ? 'after closing dips' : litres(d.total_variance)"
				:tone="missingDips.length ? '' : d.total_variance < 0 ? 'bad' : 'good'"
			/>
		</div>
		<p class="mt-2 text-[12px] text-ink-3">
			On submit, ERPNext tank stock is reconciled to the physical closing dip.
		</p>
		<Section title="Remarks" class="mt-4">
			<textarea v-model="d.remarks" class="inp h-16 py-2" :disabled="!ed" />
		</Section>
	</div>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
import { toast } from "frappe-ui";
import { useDocForm, nextKey } from "../composables/useDocForm";
import { api, errorText, printUrl } from "../api";
import { session } from "../session";
import { num, litres, dateFmt, today, addDays, flt } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
import AutoField from "../components/AutoField.vue";
import NumInput from "../components/NumInput.vue";
import FuelChip from "../components/FuelChip.vue";
import StatusPill from "../components/StatusPill.vue";
import FormActions from "../components/FormActions.vue";

const props = defineProps({ name: String });
const fetching = ref(false);
const f = useDocForm({
	doctype: "Daily Stock Register",
	name: props.name,
	route: "/dsr",
	tables: ["items"],
	blank: () => ({
		doctype: "Daily Stock Register",
		station: session.station,
		posting_date: new Date().getHours() < 12 ? addDays(today(), -1) : today(),
		items: [],
	}),
});
const d = computed(() => f.doc.value);
const ed = computed(() => f.editable.value);
const missingDips = computed(() =>
	d.value.items.filter((r) => !flt(r.closing_stock) && !flt(r.closing_dip_mm)).map((r) => r.tank)
);
const hasClosing = (r) => flt(r.closing_stock) || flt(r.closing_dip_mm);
const beyond = computed(() => d.value.items.filter((r) => !r.within_limit).map((r) => r.tank));

async function fetchData() {
	fetching.value = true;
	try {
		const r = await api("fetch_dsr", {
			station: d.value.station,
			posting_date: d.value.posting_date,
		});
		d.value.items = r.items.map((x) => ({ ...x, _key: nextKey() }));
		for (const k of ["total_receipts", "total_sales", "total_variance", "all_within_limit"])
			d.value[k] = r[k];
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		fetching.value = false;
	}
}
function onDip(r) {
	r.closing_stock = 0;
	f.schedule((sd) => {
		sd.items.forEach((s, i) => {
			const x = d.value.items[i];
			if (x)
				Object.assign(x, {
					closing_stock: s.closing_stock,
					net_sales: s.net_sales,
					book_closing: s.book_closing,
					variance: s.variance,
					variance_percent: s.variance_percent,
					within_limit: s.within_limit,
					cumulative_variance: s.cumulative_variance,
				});
		});
		for (const k of ["total_receipts", "total_sales", "total_variance", "all_within_limit"])
			d.value[k] = sd[k];
	}, 400);
}
onMounted(async () => {
	await f.load();
	if (f.isNew.value) fetchData();
});
</script>
