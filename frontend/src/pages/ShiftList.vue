<template>
	<DocList
		table-from="xl"
		:search-fields="['name', 'cashier_name', 'shift']"
		search-placeholder="Search entry, cashier or shift…"
		title="Shift closing"
		subtitle="Meter readings, collections and cash for every shift"
		doctype="Shift Sale Entry"
		:fields="[
			'name',
			'posting_date',
			'shift',
			'cashier_name',
			'total_sale_qty',
			'gross_sales',
			'credit_sales_amount',
			'digital_amount',
			'expected_cash',
			'cash_counted',
			'short_excess',
			'workflow_state',
			'docstatus',
		]"
		:columns="columns"
		new-route="/shifts/new"
		new-label="New shift closing"
		route-base="/shifts"
		:statuses="['Draft', 'Pending Approval', 'Approved', 'Rejected', 'Cancelled']"
		:summary="summary"
		:sum-fields="['total_sale_qty', 'gross_sales', 'credit_sales_amount', 'short_excess']"
		empty-title="No shift closings"
	>
		<template #cell-short_excess="{ row }"
			><span
				:class="
					row.short_excess < -0.5
						? 'text-red-600 font-semibold'
						: row.short_excess > 0.5
						? 'text-amber-600'
						: 'text-green-700'
				"
				>{{ signedInr(row.short_excess) }}</span
			></template
		>
		<template #cell-workflow_state="{ row }"><StatusPill :status="state(row)" /></template>
		<template #mobile="{ row }">
			<div class="flex items-start justify-between gap-2">
				<div>
					<div class="text-[14px] font-semibold">
						{{ row.shift }} · {{ dateFmt(row.posting_date) }}
					</div>
					<div class="text-[12px] text-ink-2">
						{{ row.cashier_name }} · {{ row.name }}
					</div>
				</div>
				<StatusPill :status="state(row)" />
			</div>
			<div class="mt-2 grid grid-cols-3 gap-2 text-[12px]">
				<div>
					<div class="text-ink-3">Sale</div>
					<div class="num font-medium">{{ litres(row.total_sale_qty, 0) }}</div>
				</div>
				<div>
					<div class="text-ink-3">Gross</div>
					<div class="num font-medium">{{ compactInr(row.gross_sales) }}</div>
				</div>
				<div>
					<div class="text-ink-3">Cash</div>
					<div
						class="num font-semibold"
						:class="row.short_excess < -0.5 ? 'text-red-600' : 'text-green-700'"
					>
						{{ signedInr(row.short_excess) }}
					</div>
				</div>
			</div>
		</template>
	</DocList>
</template>
<script setup>
import DocList from "../components/DocList.vue";
import StatusPill from "../components/StatusPill.vue";
import { inr, litres, signedInr, dateFmt, compactInr, num } from "../format";
const state = (r) =>
	r.docstatus === 2 ? "Cancelled" : r.workflow_state || (r.docstatus ? "Submitted" : "Draft");
const columns = [
	{ key: "name", label: "Entry" },
	{ key: "posting_date", label: "Date", format: dateFmt },
	{ key: "shift", label: "Shift" },
	{ key: "cashier_name", label: "Cashier" },
	{ key: "total_sale_qty", label: "Sale (L)", num: true, format: (v) => num(v) },
	{ key: "gross_sales", label: "Gross", num: true, format: (v) => inr(v) },
	{ key: "credit_sales_amount", label: "Credit", num: true, format: (v) => inr(v) },
	{
		key: "digital_amount",
		label: "Digital",
		num: true,
		format: (v) => inr(v),
		cls: "hidden 2xl:table-cell",
	},
	{
		key: "cash_counted",
		label: "Cash counted",
		num: true,
		format: (v) => inr(v),
		cls: "hidden 2xl:table-cell",
	},
	{ key: "short_excess", label: "Short/Excess", num: true },
	{ key: "workflow_state", label: "Status" },
];
const summary = (rows) => {
	const live = rows.filter((r) => r.docstatus !== 2);
	const s = (f) => live.reduce((a, r) => a + (r[f] || 0), 0);
	return [
		{ label: "Fuel sold", value: litres(s("total_sale_qty"), 0) },
		{ label: "Gross sales", value: compactInr(s("gross_sales")) },
		{ label: "Credit", value: compactInr(s("credit_sales_amount")) },
		{
			label: "Net short/excess",
			value: signedInr(s("short_excess")),
			cls: s("short_excess") < 0 ? "text-red-600" : "text-green-700",
		},
	];
};
</script>
