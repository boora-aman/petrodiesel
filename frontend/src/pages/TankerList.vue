<template>
	<DocList
		:search-fields="['name', 'truck_no', 'supplier_invoice_no']"
		search-placeholder="Search lorry no or OMC invoice…"
		title="Tanker receipts"
		subtitle="Decantation with density and dip checks"
		doctype="Tanker Receipt"
		:fields="[
			'name',
			'posting_date',
			'truck_no',
			'supplier',
			'supplier_invoice_no',
			'total_invoice_qty',
			'total_received_qty',
			'total_shortage_qty',
			'total_amount',
			'workflow_state',
			'docstatus',
		]"
		:columns="columns"
		new-route="/tankers/new"
		new-label="New tanker receipt"
		route-base="/tankers"
		:days="60"
		:statuses="['Draft', 'Pending Verification', 'Accepted', 'Rejected', 'Cancelled']"
		empty-title="No tanker receipts"
	>
		<template #cell-total_shortage_qty="{ row }"
			><span
				:class="
					row.total_shortage_qty > 0.5 ? 'text-red-600 font-semibold' : 'text-green-700'
				"
				>{{ num(row.total_shortage_qty) }}</span
			></template
		>
		<template #cell-workflow_state="{ row }"
			><StatusPill
				:status="
					row.docstatus === 2
						? 'Cancelled'
						: row.workflow_state || (row.docstatus ? 'Submitted' : 'Draft')
				"
		/></template>
		<template #mobile="{ row }">
			<div class="flex justify-between gap-2">
				<div>
					<div class="text-[14px] font-semibold">{{ row.truck_no }}</div>
					<div class="text-[12px] text-ink-2">
						{{ dateFmt(row.posting_date) }} · {{ row.supplier_invoice_no }}
					</div>
				</div>
				<StatusPill
					:status="row.docstatus === 2 ? 'Cancelled' : row.workflow_state || 'Draft'"
				/>
			</div>
			<div class="mt-2 grid grid-cols-3 text-[12px]">
				<div>
					<div class="text-ink-3">Invoiced</div>
					<div class="num">{{ litres(row.total_invoice_qty, 0) }}</div>
				</div>
				<div>
					<div class="text-ink-3">Received</div>
					<div class="num">{{ litres(row.total_received_qty, 0) }}</div>
				</div>
				<div>
					<div class="text-ink-3">Short</div>
					<div
						class="num font-semibold"
						:class="row.total_shortage_qty > 0.5 ? 'text-red-600' : 'text-green-700'"
					>
						{{ litres(row.total_shortage_qty) }}
					</div>
				</div>
			</div>
		</template>
	</DocList>
</template>
<script setup>
import DocList from "../components/DocList.vue";
import StatusPill from "../components/StatusPill.vue";
import { inr, litres, dateFmt, num } from "../format";
const columns = [
	{ key: "name", label: "Receipt" },
	{ key: "posting_date", label: "Date", format: dateFmt },
	{ key: "truck_no", label: "Tank lorry" },
	{ key: "supplier_invoice_no", label: "OMC invoice" },
	{ key: "total_invoice_qty", label: "Invoiced (L)", num: true, format: (v) => num(v) },
	{ key: "total_received_qty", label: "Received (L)", num: true, format: (v) => num(v) },
	{ key: "total_shortage_qty", label: "Short (L)", num: true },
	{ key: "total_amount", label: "Amount", num: true, format: (v) => inr(v) },
	{ key: "workflow_state", label: "Status" },
];
</script>
