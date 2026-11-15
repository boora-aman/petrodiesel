<template>
	<DocList
		:search-fields="['name']"
		search-placeholder="Search DSR no…"
		title="Daily stock register"
		subtitle="Opening + receipts − sales against the closing dip"
		doctype="Daily Stock Register"
		:fields="[
			'name',
			'posting_date',
			'total_receipts',
			'total_sales',
			'total_variance',
			'all_within_limit',
			'docstatus',
		]"
		:columns="columns"
		new-route="/dsr/new"
		new-label="New DSR"
		route-base="/dsr"
		empty-title="No registers"
	>
		<template #cell-total_variance="{ row }"
			><span :class="row.total_variance < 0 ? 'text-red-600' : 'text-green-700'">{{
				num(row.total_variance)
			}}</span></template
		>
		<template #cell-all_within_limit="{ row }"
			><StatusPill
				:status="row.all_within_limit ? 'Within limit' : 'Beyond limit'"
				:tone="row.all_within_limit ? 'green' : 'red'"
		/></template>
		<template #cell-docstatus="{ row }"
			><StatusPill :status="['Draft', 'Submitted', 'Cancelled'][row.docstatus]"
		/></template>
		<template #mobile="{ row }">
			<div class="flex justify-between">
				<div class="text-[14px] font-semibold">{{ dateFmt(row.posting_date) }}</div>
				<StatusPill
					:status="row.all_within_limit ? 'Within limit' : 'Beyond limit'"
					:tone="row.all_within_limit ? 'green' : 'red'"
				/>
			</div>
			<div class="mt-1 text-[12px]">
				Sales {{ litres(row.total_sales, 0) }} · Receipts
				{{ litres(row.total_receipts, 0) }} ·
				<span :class="row.total_variance < 0 ? 'text-red-600' : 'text-green-700'"
					>{{ num(row.total_variance) }} L</span
				>
			</div>
		</template>
	</DocList>
</template>
<script setup>
import DocList from "../components/DocList.vue";
import StatusPill from "../components/StatusPill.vue";
import { litres, dateFmt, num } from "../format";
const columns = [
	{ key: "name", label: "DSR" },
	{ key: "posting_date", label: "Date", format: dateFmt },
	{ key: "total_receipts", label: "Receipts (L)", num: true, format: (v) => num(v) },
	{ key: "total_sales", label: "Net sales (L)", num: true, format: (v) => num(v) },
	{ key: "total_variance", label: "Gain/Loss (L)", num: true },
	{ key: "all_within_limit", label: "Loss check" },
	{ key: "docstatus", label: "Status" },
];
</script>
