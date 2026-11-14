<template>
	<DocList
		title="Stock transfers"
		subtitle="Between shop stores, or tank to tank"
		doctype="Internal Stock Transfer"
		:days="60"
		:fields="[
			'name',
			'posting_date',
			'transfer_type',
			'from_warehouse',
			'to_warehouse',
			'docstatus',
		]"
		:columns="columns"
		new-route="/transfers/new"
		new-label="New transfer"
		route-base="/transfers"
		status-field="transfer_type"
		:statuses="['Lube / Shop Stock', 'Fuel Tank to Tank']"
		:search-fields="['name', 'from_warehouse', 'to_warehouse']"
		search-placeholder="Search transfer or warehouse…"
		empty-title="No transfers"
	>
		<template #cell-docstatus="{ row }"
			><StatusPill :status="['Draft', 'Submitted', 'Cancelled'][row.docstatus]"
		/></template>
		<template #mobile="{ row }"
			><div class="font-semibold">{{ row.from_warehouse }} → {{ row.to_warehouse }}</div>
			<div class="text-[12px] text-ink-2">
				{{ dateFmt(row.posting_date) }} · {{ row.transfer_type }}
			</div></template
		>
	</DocList>
</template>
<script setup>
import DocList from "../components/DocList.vue";
import StatusPill from "../components/StatusPill.vue";
import { dateFmt } from "../format";
const columns = [
	{ key: "name", label: "Transfer" },
	{ key: "posting_date", label: "Date", format: dateFmt },
	{ key: "transfer_type", label: "Type" },
	{ key: "from_warehouse", label: "From" },
	{ key: "to_warehouse", label: "To" },
	{ key: "docstatus", label: "Status" },
];
</script>
