<template>
	<DocList
		title="Shop purchases"
		subtitle="Lubricants and accessories bought into the shop store"
		doctype="Shop Purchase"
		:days="60"
		:fields="[
			'name',
			'posting_date',
			'supplier',
			'bill_no',
			'total_qty',
			'total_amount',
			'docstatus',
		]"
		:columns="columns"
		new-route="/purchases/new"
		new-label="New purchase"
		route-base="/purchases"
		status-field="docstatus"
		:search-fields="['name', 'supplier', 'bill_no']"
		search-placeholder="Search supplier or bill no…"
		empty-title="No shop purchases"
	>
		<template #cell-docstatus="{ row }"
			><StatusPill :status="['Draft', 'Submitted', 'Cancelled'][row.docstatus]"
		/></template>
		<template #mobile="{ row }"
			><div class="flex justify-between">
				<div>
					<div class="font-semibold">{{ row.supplier }}</div>
					<div class="text-[12px] text-ink-2">
						{{ dateFmt(row.posting_date) }} · {{ row.bill_no }}
					</div>
				</div>
				<span class="num font-semibold">{{ inr(row.total_amount) }}</span>
			</div></template
		>
	</DocList>
</template>
<script setup>
import DocList from "../components/DocList.vue";
import StatusPill from "../components/StatusPill.vue";
import { inr, dateFmt, num } from "../format";
const columns = [
	{ key: "name", label: "Purchase" },
	{ key: "posting_date", label: "Date", format: dateFmt },
	{ key: "supplier", label: "Supplier" },
	{ key: "bill_no", label: "Bill no" },
	{ key: "total_qty", label: "Qty", num: true, format: (v) => num(v, 0) },
	{ key: "total_amount", label: "Amount", num: true, format: (v) => inr(v) },
	{ key: "docstatus", label: "Status" },
];
</script>
