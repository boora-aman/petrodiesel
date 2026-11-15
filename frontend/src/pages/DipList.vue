<template>
	<DocList
		:search-fields="['name', 'reading_type']"
		search-placeholder="Search reading…"
		title="Tank dips"
		subtitle="Physical stock by dip rod, water paste and density"
		doctype="Tank Dip Reading"
		:fields="[
			'name',
			'posting_date',
			'posting_time',
			'reading_type',
			'total_dip_stock',
			'total_book_stock',
			'total_variance',
			'docstatus',
		]"
		:columns="columns"
		new-route="/dips/new"
		new-label="New dip reading"
		route-base="/dips"
		status-field="reading_type"
		:statuses="[
			'Morning (Opening)',
			'Night (Closing)',
			'Shift Change',
			'Before Decantation',
			'After Decantation',
			'Surprise Check',
		]"
		empty-title="No dip readings"
	>
		<template #cell-total_variance="{ row }"
			><span :class="row.total_variance < -0.5 ? 'text-red-600' : 'text-green-700'">{{
				num(row.total_variance)
			}}</span></template
		>
		<template #cell-docstatus="{ row }"
			><StatusPill :status="['Draft', 'Submitted', 'Cancelled'][row.docstatus]"
		/></template>
		<template #mobile="{ row }">
			<div class="flex justify-between">
				<div>
					<div class="text-[14px] font-semibold">{{ row.reading_type }}</div>
					<div class="text-[12px] text-ink-2">
						{{ dateFmt(row.posting_date) }} {{ timeFmt(row.posting_time) }}
					</div>
				</div>
				<StatusPill :status="['Draft', 'Submitted', 'Cancelled'][row.docstatus]" />
			</div>
			<div class="mt-1 text-[12px]">
				Dip {{ litres(row.total_dip_stock, 0) }} · Book
				{{ litres(row.total_book_stock, 0) }} ·
				<span :class="row.total_variance < -0.5 ? 'text-red-600' : 'text-green-700'"
					>{{ num(row.total_variance) }} L</span
				>
			</div>
		</template>
	</DocList>
</template>
<script setup>
import DocList from "../components/DocList.vue";
import StatusPill from "../components/StatusPill.vue";
import { litres, dateFmt, timeFmt, num } from "../format";
const columns = [
	{ key: "name", label: "Reading" },
	{ key: "posting_date", label: "Date", format: dateFmt },
	{ key: "posting_time", label: "Time", format: timeFmt },
	{ key: "reading_type", label: "Type" },
	{ key: "total_dip_stock", label: "Dip stock (L)", num: true, format: (v) => num(v) },
	{ key: "total_book_stock", label: "Book stock (L)", num: true, format: (v) => num(v) },
	{ key: "total_variance", label: "Variance (L)", num: true },
	{ key: "docstatus", label: "Status" },
];
</script>
