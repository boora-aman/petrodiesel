<template>
	<div v-if="f.doc.value">
		<PageHeader
			:title="f.isNew.value ? 'New shop purchase' : d.name"
			back="/purchases"
			:subtitle="d.supplier || 'Lubricants & accessories'"
		>
			<template #badge><StatusPill :status="f.state.value" /></template>
			<template #actions><FormActions :form="f" /></template>
		</PageHeader>
		<div class="card card-pad mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
			<Field label="Supplier" required class="col-span-2"
				><LinkInput v-model="d.supplier" doctype="Supplier" :disabled="!ed"
			/></Field>
			<Field label="Supplier bill no" required
				><input v-model="d.bill_no" class="inp" :disabled="!ed"
			/></Field>
			<Field label="Bill date"
				><input v-model="d.bill_date" type="date" class="inp" :disabled="!ed"
			/></Field>
			<Field label="Posting date"
				><input v-model="d.posting_date" type="date" class="inp" :disabled="!ed"
			/></Field>
			<Field label="Into warehouse" class="col-span-2"
				><LinkInput
					v-model="d.warehouse"
					doctype="Warehouse"
					:filters="{ is_group: 0 }"
					:disabled="!ed"
			/></Field>
			<Field label="GST template (optional)"
				><LinkInput
					v-model="d.taxes_and_charges"
					doctype="Purchase Taxes and Charges Template"
					:disabled="!ed"
			/></Field>
		</div>
		<Section title="Items">
			<template #actions
				><button
					v-if="ed"
					class="btn-secondary btn-sm"
					@click="d.items.push({ qty: 1, rate: 0, _key: nextKey() })"
				>
					<i class="lucide-plus size-3.5" />Add item
				</button></template
			>
			<div v-for="r in d.items" :key="r._key" class="mb-2 grid grid-cols-12 items-end gap-2">
				<div class="col-span-12 sm:col-span-5">
					<Field label="Item"
						><LinkInput
							v-model="r.item_code"
							doctype="Item"
							:filters="{
								petro_product_type: ['in', ['Lubricant', 'Accessory', 'Other']],
							}"
							:disabled="!ed"
							@change="onItem(r)"
					/></Field>
				</div>
				<div class="col-span-3 sm:col-span-2">
					<Field label="Qty"
						><NumInput v-model="r.qty" :disabled="!ed" @update:model-value="calc"
					/></Field>
				</div>
				<div class="col-span-4 sm:col-span-2">
					<Field label="Rate"
						><NumInput v-model="r.rate" :disabled="!ed" @update:model-value="calc"
					/></Field>
				</div>
				<div class="col-span-4 sm:col-span-2">
					<AutoField label="Amount" :value="num(r.amount)" />
				</div>
				<button
					v-if="ed"
					class="col-span-1 pb-2 text-red-600"
					title="Remove"
					@click="
						d.items.splice(d.items.indexOf(r), 1);
						calc();
					"
				>
					<i class="lucide-trash-2 size-4" />
				</button>
			</div>
			<div class="mt-3 flex justify-end gap-6 text-[13px]">
				<span
					>Qty <b class="num">{{ num(d.total_qty, 0) }}</b></span
				><span
					>Total <b class="num">{{ inr(d.total_amount) }}</b></span
				>
			</div>
		</Section>
		<a
			v-if="d.purchase_invoice"
			:href="deskUrl('Purchase Invoice', d.purchase_invoice)"
			target="_blank"
			class="mt-3 inline-flex text-[13px] text-brand-600 hover:underline"
			>Purchase Invoice {{ d.purchase_invoice }} →</a
		>
	</div>
</template>
<script setup>
import { computed, onMounted } from "vue";
import { useDocForm, nextKey } from "../composables/useDocForm";
import { getList, deskUrl } from "../api";
import { session } from "../session";
import { inr, num, today, flt } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
import AutoField from "../components/AutoField.vue";
import NumInput from "../components/NumInput.vue";
import LinkInput from "../components/LinkInput.vue";
import StatusPill from "../components/StatusPill.vue";
import FormActions from "../components/FormActions.vue";
const props = defineProps({ name: String });
const f = useDocForm({
	doctype: "Shop Purchase",
	name: props.name,
	route: "/purchases",
	tables: ["items"],
	blank: async () => ({
		doctype: "Shop Purchase",
		station: session.station,
		posting_date: today(),
		bill_date: today(),
		warehouse: (
			await getList("Fuel Station", {
				filters: { name: session.station },
				fields: ["lube_warehouse"],
			})
		)[0]?.lube_warehouse,
		items: [{ qty: 1, rate: 0 }],
	}),
});
const d = computed(() => f.doc.value);
const ed = computed(() => f.editable.value);
function calc() {
	d.value.items.forEach((r) => (r.amount = flt(flt(r.qty) * flt(r.rate))));
	d.value.total_qty = d.value.items.reduce((a, r) => a + flt(r.qty), 0);
	d.value.total_amount = flt(d.value.items.reduce((a, r) => a + flt(r.amount), 0));
}
async function onItem(r) {
	const it = (
		await getList("Item", {
			filters: { name: r.item_code },
			fields: ["last_purchase_rate", "valuation_rate"],
		})
	)[0];
	if (!r.rate) r.rate = flt(it?.last_purchase_rate || it?.valuation_rate);
	calc();
}
onMounted(async () => {
	await f.load();
	calc();
});
</script>
