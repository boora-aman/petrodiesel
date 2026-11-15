<template>
	<div>
		<PageHeader
			title="Approvals"
			subtitle="Shift closings and tanker receipts waiting for you"
		/>
		<div class="mb-4 flex gap-1 border-b border-line">
			<button class="tab-btn" :class="{ active: tab === 'shifts' }" @click="tab = 'shifts'">
				Shift closings <span class="text-ink-3">({{ shifts.length }})</span>
			</button>
			<button
				class="tab-btn"
				:class="{ active: tab === 'tankers' }"
				@click="tab = 'tankers'"
			>
				Tanker receipts <span class="text-ink-3">({{ tankers.length }})</span>
			</button>
			<button
				v-if="tab === 'shifts' && withinTol.length > 1"
				class="btn-secondary btn-sm mb-1 ml-auto"
				:disabled="busy"
				@click="bulk"
			>
				Approve {{ withinTol.length }} within tolerance
			</button>
		</div>
		<div v-if="loading"><Skeleton class="h-32 w-full" /></div>
		<EmptyState
			v-else-if="!(tab === 'shifts' ? shifts : tankers).length"
			title="All caught up"
			text="Nothing is waiting for approval."
			icon="lucide-circle-check"
		/>
		<div class="grid grid-cols-1 gap-3 lg:grid-cols-2">
			<div v-for="r in tab === 'shifts' ? shifts : []" :key="r.name" class="card card-pad">
				<div class="flex justify-between">
					<div>
						<div class="text-[14px] font-semibold">
							{{ r.shift }} · {{ dateFmt(r.posting_date) }}
						</div>
						<div class="text-[12px] text-ink-2">
							{{ r.cashier_name }} · {{ r.name }}
						</div>
					</div>
					<span
						class="num text-[15px] font-semibold"
						:class="r.short_excess < -0.5 ? 'text-red-600' : 'text-green-700'"
						>{{ signedInr(r.short_excess) }}</span
					>
				</div>
				<div class="mt-3 grid grid-cols-3 gap-2 text-[12px]">
					<div>
						<div class="text-ink-3">Sale</div>
						<b class="num">{{ litres(r.total_sale_qty, 0) }}</b>
					</div>
					<div>
						<div class="text-ink-3">Gross</div>
						<b class="num">{{ compactInr(r.gross_sales) }}</b>
					</div>
					<div>
						<div class="text-ink-3">Credit</div>
						<b class="num">{{ compactInr(r.credit_sales_amount) }}</b>
					</div>
				</div>
				<div
					v-if="r.remarks"
					class="mt-2 rounded bg-slate-50 px-2 py-1 text-[12px] text-ink-2"
				>
					“{{ r.remarks }}”
				</div>
				<div class="mt-3 flex gap-2">
					<RouterLink :to="`/shifts/${r.name}`" class="btn-secondary btn-sm"
						>Open</RouterLink
					>
					<button
						class="btn-secondary btn-sm !text-red-600"
						@click="reject('Shift Sale Entry', r.name)"
					>
						Reject
					</button>
					<button
						class="btn-primary btn-sm ml-auto"
						:disabled="busy"
						@click="approve('Shift Sale Entry', r.name, 'Approve')"
					>
						Approve
					</button>
				</div>
			</div>
			<div v-for="r in tab === 'tankers' ? tankers : []" :key="r.name" class="card card-pad">
				<div class="flex justify-between">
					<div>
						<div class="text-[14px] font-semibold">
							{{ r.truck_no }} · {{ dateFmt(r.posting_date) }}
						</div>
						<div class="text-[12px] text-ink-2">
							{{ r.supplier_invoice_no }} · {{ r.name }}
						</div>
					</div>
					<span
						class="num text-[14px] font-semibold"
						:class="r.total_shortage_qty > 0.5 ? 'text-red-600' : 'text-green-700'"
						>{{ litres(r.total_shortage_qty) }} short</span
					>
				</div>
				<div class="mt-3 grid grid-cols-3 text-[12px]">
					<div>
						<div class="text-ink-3">Invoiced</div>
						<b class="num">{{ litres(r.total_invoice_qty, 0) }}</b>
					</div>
					<div>
						<div class="text-ink-3">Received</div>
						<b class="num">{{ litres(r.total_received_qty, 0) }}</b>
					</div>
					<div>
						<div class="text-ink-3">Amount</div>
						<b class="num">{{ compactInr(r.total_amount) }}</b>
					</div>
				</div>
				<div class="mt-3 flex gap-2">
					<RouterLink :to="`/tankers/${r.name}`" class="btn-secondary btn-sm"
						>Open</RouterLink
					>
					<button
						class="btn-secondary btn-sm !text-red-600"
						@click="reject('Tanker Receipt', r.name)"
					>
						Reject
					</button>
					<button
						class="btn-primary btn-sm ml-auto"
						:disabled="busy"
						@click="approve('Tanker Receipt', r.name, 'Accept')"
					>
						Accept
					</button>
				</div>
			</div>
		</div>
		<Modal v-model="rej.open" title="Reject">
			<Field label="Reason" required>
				<textarea v-model="rej.reason" class="inp h-24 py-2" />
			</Field>
			<template #footer
				><button class="btn-secondary" @click="rej.open = false">Close</button
				><button class="btn-danger" :disabled="!rej.reason" @click="doReject">
					Reject
				</button></template
			>
		</Modal>
	</div>
</template>
<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { toast } from "frappe-ui";
import { api, errorText } from "../api";
import { session, refreshCounts } from "../session";
import { litres, signedInr, compactInr, dateFmt } from "../format";
import PageHeader from "../components/PageHeader.vue";
import EmptyState from "../components/EmptyState.vue";
import Skeleton from "../components/Skeleton.vue";
import Modal from "../components/Modal.vue";
import Field from "../components/Field.vue";

const tab = ref("shifts");
const shifts = ref([]);
const tankers = ref([]);
const loading = ref(true);
const busy = ref(false);
const rej = reactive({ open: false, doctype: "", name: "", reason: "" });
// tolerance 0 = no remarks rule on the server; bulk approval then takes only tallied shifts
const tol = computed(() => Number(session.boot.settings?.cash_variance_tolerance) || 0);
const withinTol = computed(() =>
	shifts.value.filter((r) => Math.abs(r.short_excess) <= Math.max(tol.value, 1))
);
const shiftSeq = (s) => (session.boot.shifts || []).find((x) => x.name === s)?.sequence || 0;
async function load() {
	loading.value = true;
	let a = { rows: [] },
		b = { rows: [] };
	try {
		[a, b] = await Promise.all([
			api("list_docs", {
				doctype: "Shift Sale Entry",
				filters: { workflow_state: "Pending Approval", docstatus: 0 },
				fields: [
					"name",
					"posting_date",
					"shift",
					"cashier_name",
					"total_sale_qty",
					"gross_sales",
					"credit_sales_amount",
					"short_excess",
					"remarks",
				],
			}),
			api("list_docs", {
				doctype: "Tanker Receipt",
				filters: { workflow_state: "Pending Verification", docstatus: 0 },
				fields: [
					"name",
					"posting_date",
					"truck_no",
					"supplier_invoice_no",
					"total_invoice_qty",
					"total_received_qty",
					"total_shortage_qty",
					"total_amount",
				],
			}),
		]);
	} catch (e) {
		toast.error(errorText(e));
	}
	shifts.value = a.rows;
	tankers.value = b.rows;
	loading.value = false;
	refreshCounts();
}
async function approve(doctype, name, action) {
	if (busy.value) return;
	busy.value = true;
	try {
		await api("doc_action", { doctype, name, action });
		toast.success(`${name} ${action === "Accept" ? "accepted" : "approved"} and posted`);
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
		load();
	}
}
async function bulk() {
	if (busy.value) return;
	busy.value = true;
	let ok = 0,
		failed = 0;
	// earlier shifts first: openings must chain from the previous approved closing
	const rows = [...withinTol.value].sort(
		(a, b) =>
			a.posting_date.localeCompare(b.posting_date) ||
			shiftSeq(a.shift) - shiftSeq(b.shift) ||
			a.name.localeCompare(b.name)
	);
	for (const r of rows) {
		try {
			await api("doc_action", {
				doctype: "Shift Sale Entry",
				name: r.name,
				action: "Approve",
			});
			ok++;
		} catch (e) {
			failed++;
			toast.error(`${r.name}: ${errorText(e)}`);
		}
	}
	busy.value = false;
	if (ok) toast.success(`${ok} shift${ok > 1 ? "s" : ""} approved and posted`);
	if (failed && !ok) toast.error("No shift could be approved. See the messages above.");
	load();
}
function reject(doctype, name) {
	Object.assign(rej, { open: true, doctype, name, reason: "" });
}
async function doReject() {
	if (busy.value) return;
	if (!rej.reason.trim()) {
		toast.error("Enter the reason for rejection.");
		return;
	}
	busy.value = true;
	try {
		await api("doc_action", {
			doctype: rej.doctype,
			name: rej.name,
			action: "Reject",
			reason: rej.reason,
		});
		toast.success("Rejected");
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
	rej.open = false;
	load();
}
onMounted(load);
</script>
