<template>
	<div v-if="f.doc.value">
		<PageHeader
			:title="f.isNew.value ? 'New credit bill' : d.name"
			back="/credit-bills"
			:subtitle="d.customer || 'Choose customer and period'"
		>
			<template #badge><StatusPill :status="f.state.value" /></template>
			<template #actions
				><FormActions
					:form="f"
					:print-url="
						!f.isNew.value ? printUrl('Credit Bill', d.name, 'Credit Bill') : ''
					"
					:blocked="!!problem"
					:blocked-reason="problem"
			/></template>
		</PageHeader>
		<div class="card card-pad mb-4 grid grid-cols-2 gap-3 md:grid-cols-5">
			<Field label="Customer" required class="col-span-2"
				><LinkInput v-model="d.customer" doctype="Customer" :disabled="!ed"
			/></Field>
			<Field label="From" required
				><input
					v-model="d.from_date"
					type="date"
					class="inp"
					:max="d.to_date || undefined"
					:disabled="!ed"
			/></Field>
			<Field label="To" required
				><input
					v-model="d.to_date"
					type="date"
					class="inp"
					:min="d.from_date || undefined"
					:disabled="!ed"
			/></Field>
			<div class="flex items-end">
				<button
					v-if="ed"
					class="btn-primary w-full"
					:disabled="!d.customer || badPeriod || busy"
					@click="fetch"
				>
					<i class="lucide-download size-4" />Fetch entries
				</button>
			</div>
			<Field label="Bill date"
				><input v-model="d.bill_date" type="date" class="inp" :disabled="!ed"
			/></Field>
			<Field label="Due date"
				><input v-model="d.due_date" type="date" class="inp" :disabled="!ed"
			/></Field>
		</div>
		<div
			v-if="ed && problem"
			class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] text-amber-800"
		>
			{{ problem }}
		</div>
		<div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
			<AutoField label="Opening balance" :value="inr(d.opening_balance)" /><AutoField
				label="Billed"
				:value="inr(d.total_billed)"
			/>
			<AutoField label="Received" :value="inr(d.total_received)" /><AutoField
				label="Litres"
				:value="num(d.total_qty)"
			/>
			<AutoField label="Amount due" :value="inr(d.closing_balance)" big />
		</div>
		<Section title="Fuel & items billed" flush class="mb-4">
			<EmptyState
				v-if="!d.items.length"
				title="No entries"
				text="Choose customer and period, then fetch."
			/>
			<div v-else class="max-h-[50vh] overflow-auto">
				<table class="tbl">
					<thead class="sticky top-0">
						<tr>
							<th>Date</th>
							<th>Invoice</th>
							<th>Vehicle</th>
							<th>Slip</th>
							<th>Item</th>
							<th class="!text-right">Qty</th>
							<th class="!text-right">Rate</th>
							<th class="!text-right">Amount</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="r in d.items" :key="r._key">
							<td>{{ dateFmt(r.posting_date) }}</td>
							<td class="text-[12px]">{{ r.sales_invoice }}</td>
							<td>{{ r.vehicle }}</td>
							<td>{{ r.slip_no }}</td>
							<td>{{ r.item_code }}</td>
							<td class="r">{{ r.qty ? num(r.qty) : "" }}</td>
							<td class="r">{{ r.rate ? num(r.rate) : "" }}</td>
							<td class="r font-medium">{{ inr(r.amount) }}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</Section>
		<Section title="Payments received" flush>
			<EmptyState v-if="!d.payments.length" title="No payments in this period" />
			<div v-else class="overflow-x-auto">
				<table class="tbl">
					<thead>
						<tr>
							<th>Date</th>
							<th>Voucher</th>
							<th>Mode</th>
							<th class="!text-right">Amount</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="p in d.payments" :key="p._key">
							<td>{{ dateFmt(p.posting_date) }}</td>
							<td class="text-[12px]">{{ p.voucher_type }} {{ p.voucher_no }}</td>
							<td>{{ p.mode_of_payment }}</td>
							<td class="r text-green-700">{{ inr(p.amount) }}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</Section>
	</div>
</template>
<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { toast } from "frappe-ui";
import { useDocForm, nextKey } from "../composables/useDocForm";
import { api, errorText, printUrl } from "../api";
import { session } from "../session";
import { inr, num, dateFmt, today, addDays } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
import AutoField from "../components/AutoField.vue";
import LinkInput from "../components/LinkInput.vue";
import StatusPill from "../components/StatusPill.vue";
import EmptyState from "../components/EmptyState.vue";
import FormActions from "../components/FormActions.vue";
const props = defineProps({ name: String });
const busy = ref(false);
const f = useDocForm({
	doctype: "Credit Bill",
	name: props.name,
	route: "/credit-bills",
	tables: ["items", "payments"],
	blank: () => ({
		doctype: "Credit Bill",
		station: session.station,
		customer: new URLSearchParams(location.search).get("customer") || "",
		from_date: addDays(today(), -15),
		to_date: today(),
		bill_date: today(),
		items: [],
		payments: [],
	}),
});
const d = computed(() => f.doc.value);
const ed = computed(() => f.editable.value);
// entries shown belong to the customer/period they were fetched for
const stale = ref(false);
let ready = false;
let timer;
const badPeriod = computed(
	() => !!(d.value?.from_date && d.value?.to_date && d.value.from_date > d.value.to_date)
);
const problem = computed(() => {
	if (!d.value.customer) return "Choose the customer.";
	if (!d.value.from_date || !d.value.to_date) return "Choose the billing period.";
	if (badPeriod.value) return "From date is after To date.";
	if (busy.value) return "Fetching entries...";
	if (stale.value) return "Customer or period changed: fetch entries again.";
	return "";
});
const TOTALS = [
	"opening_balance",
	"total_billed",
	"total_received",
	"closing_balance",
	"total_qty",
];
watch(
	() => [d.value?.customer, d.value?.from_date, d.value?.to_date],
	(now, before) => {
		if (!ready || !ed.value || !before || now.join("|") === before.join("|")) return;
		d.value.items = [];
		d.value.payments = [];
		for (const k of TOTALS) d.value[k] = 0;
		stale.value = true;
		clearTimeout(timer);
		if (d.value.customer && d.value.from_date && d.value.to_date && !badPeriod.value)
			timer = setTimeout(fetch, 500);
	}
);
async function fetch() {
	if (!d.value.customer || badPeriod.value) return;
	clearTimeout(timer);
	busy.value = true;
	try {
		const r = await api("preview", { doc: { ...f.payload(), items: [], payments: [] } });
		if (r.error) toast.error(r.error);
		const x = r.doc;
		if (!x) return;
		d.value.items = (x.items || []).map((i) => ({ ...i, _key: nextKey() }));
		d.value.payments = (x.payments || []).map((i) => ({ ...i, _key: nextKey() }));
		for (const k of [...TOTALS, "due_date"]) d.value[k] = x[k];
		stale.value = false;
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
}
onMounted(async () => {
	await f.load();
	await nextTick();
	ready = true;
	if (f.isNew.value && d.value?.customer) fetch();
});
</script>
