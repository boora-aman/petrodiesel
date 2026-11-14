<template>
	<DocList
		title="Credit bills"
		subtitle="Periodic consolidated bills for credit customers"
		doctype="Credit Bill"
		date-field="bill_date"
		:days="90"
		:fields="[
			'name',
			'customer',
			'from_date',
			'to_date',
			'bill_date',
			'total_qty',
			'total_billed',
			'total_received',
			'closing_balance',
			'docstatus',
		]"
		:columns="columns"
		new-route="/credit-bills/new"
		new-label="New bill"
		route-base="/credit-bills"
		status-field="docstatus"
		:search-fields="['name', 'customer']"
		search-placeholder="Search bill or customer…"
		empty-title="No credit bills"
	>
		<template #cell-docstatus="{ row }"
			><StatusPill :status="['Draft', 'Submitted', 'Cancelled'][row.docstatus]"
		/></template>
		<template #mobile="{ row }">
			<div class="flex justify-between">
				<div>
					<div class="text-[14px] font-semibold">{{ row.customer }}</div>
					<div class="text-[12px] text-ink-2">
						{{ dateFmt(row.from_date) }} – {{ dateFmt(row.to_date) }}
					</div>
				</div>
				<span class="num font-semibold">{{ inr(row.closing_balance) }}</span>
			</div>
		</template>
	</DocList>
</template>
<script setup>
import DocList from "../components/DocList.vue";
import StatusPill from "../components/StatusPill.vue";
import { inr, dateFmt, num } from "../format";
const columns = [
	{ key: "name", label: "Bill" },
	{ key: "customer", label: "Customer" },
	{ key: "bill_date", label: "Bill date", format: dateFmt },
	{
		key: "from_date",
		label: "Period",
		format: (v, r) => `${dateFmt(r.from_date)} – ${dateFmt(r.to_date)}`,
		sort: false,
	},
	{ key: "total_qty", label: "Litres", num: true, format: (v) => num(v) },
	{ key: "total_billed", label: "Billed", num: true, format: (v) => inr(v) },
	{ key: "total_received", label: "Received", num: true, format: (v) => inr(v) },
	{ key: "closing_balance", label: "Amount due", num: true, format: (v) => inr(v) },
	{ key: "docstatus", label: "Status" },
];
</script>
