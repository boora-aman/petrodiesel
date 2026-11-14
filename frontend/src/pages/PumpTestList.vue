<template>
	<DocList
		:search-fields="['name', 'test_type']"
		search-placeholder="Search test…"
		title="Pump tests"
		subtitle="5 litre measure checks (±15 ml)"
		doctype="Pump Test Log"
		:fields="['name', 'posting_date', 'posting_time', 'test_type', 'all_passed', 'docstatus']"
		:columns="columns"
		new-route="/pump-tests/new"
		new-label="New pump test"
		route-base="/pump-tests"
		status-field="test_type"
		:statuses="[
			'Daily Check',
			'Customer Request',
			'W&M Inspection',
			'OMC Inspection',
			'After Repair / Calibration',
		]"
		empty-title="No pump tests"
	>
		<template #cell-all_passed="{ row }"
			><StatusPill :status="row.all_passed ? 'Pass' : 'Fail'"
		/></template>
		<template #cell-docstatus="{ row }"
			><StatusPill :status="['Draft', 'Submitted', 'Cancelled'][row.docstatus]"
		/></template>
		<template #mobile="{ row }">
			<div class="flex justify-between">
				<div>
					<div class="text-[14px] font-semibold">{{ row.test_type }}</div>
					<div class="text-[12px] text-ink-2">
						{{ dateFmt(row.posting_date) }} {{ timeFmt(row.posting_time) }}
					</div>
				</div>
				<StatusPill :status="row.all_passed ? 'Pass' : 'Fail'" />
			</div>
		</template>
	</DocList>
</template>
<script setup>
import DocList from "../components/DocList.vue";
import StatusPill from "../components/StatusPill.vue";
import { dateFmt, timeFmt } from "../format";
const columns = [
	{ key: "name", label: "Log" },
	{ key: "posting_date", label: "Date", format: dateFmt },
	{ key: "posting_time", label: "Time", format: timeFmt },
	{ key: "test_type", label: "Type" },
	{ key: "all_passed", label: "Result" },
	{ key: "docstatus", label: "Status" },
];
</script>
