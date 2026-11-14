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
			/></template>
		</PageHeader>
		<div class="card card-pad mb-4 grid grid-cols-2 gap-3 md:grid-cols-5">
			<Field label="Customer" required class="col-span-2"
				><LinkInput v-model="d.customer" doctype="Customer" :disabled="!ed"
			/></Field>
			<Field label="From" required
				><input v-model="d.from_date" type="date" class="inp" :disabled="!ed"
			/></Field>
			<Field label="To" required
				><input v-model="d.to_date" type="date" class="inp" :disabled="!ed"
			/></Field>
			<div class="flex items-end">
				<button
					v-if="ed"
					class="btn-primary w-full"
					:disabled="!d.customer || busy"
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
			<table v-else class="tbl">
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
		</Section>
	</div>
</template>
<script setup>
import { computed, onMounted, ref } from "vue";
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
async function fetch() {
	busy.value = true;
	try {
		const r = await api("preview", { doc: { ...f.payload(), items: [], payments: [] } });
		if (r.error) toast.error(r.error);
		const x = r.doc;
		d.value.items = (x.items || []).map((i) => ({ ...i, _key: nextKey() }));
		d.value.payments = (x.payments || []).map((i) => ({ ...i, _key: nextKey() }));
		for (const k of [
			"opening_balance",
			"total_billed",
			"total_received",
			"closing_balance",
			"total_qty",
			"due_date",
		])
			d.value[k] = x[k];
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
}
onMounted(async () => {
	await f.load();
	if (f.isNew.value && d.value.customer) fetch();
});
</script>
