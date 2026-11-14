<template>
	<div>
		<PageHeader :title="customer" back="/credit" subtitle="Credit customer">
			<template #actions>
				<RouterLink
					v-if="can('Credit Bill', 'create')"
					:to="`/credit-bills/new?customer=${encodeURIComponent(customer)}`"
					class="btn-secondary"
					><i class="lucide-file-text size-4" />Create bill</RouterLink
				>
				<button
					v-if="can('Payment Entry', 'create')"
					class="btn-primary"
					@click="payOpen = true"
				>
					<i class="lucide-hand-coins size-4" />Receive payment
				</button>
			</template>
		</PageHeader>
		<div v-if="data" class="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
			<KpiCard
				label="Outstanding"
				:value="inr(s.outstanding)"
				:tone="s.used_pct >= 100 ? 'bad' : 'neutral'"
			/>
			<KpiCard label="Credit limit" :value="s.limit ? inr(s.limit, true) : 'No limit'" />
			<KpiCard
				label="Available credit"
				:value="s.limit ? inr(s.available, true) : '—'"
				:tone="s.available < 0 ? 'bad' : 'neutral'"
			/>
			<KpiCard
				label="Oldest unpaid"
				:value="s.overdue_days + ' days'"
				:caption="'Last payment ' + (dateFmt(s.last_payment) || '—')"
			/>
		</div>
		<div class="no-scrollbar mb-3 flex gap-1 overflow-x-auto border-b border-line">
			<button
				v-for="tb in tabs"
				:key="tb"
				class="tab-btn"
				:class="{ active: tab === tb }"
				@click="tab = tb"
			>
				{{ tb }}
			</button>
		</div>

		<div v-if="tab === 'Statement'">
			<div class="mb-3 flex flex-wrap items-end gap-2">
				<Field label="From"
					><input v-model="from" type="date" class="inp w-40" @change="load"
				/></Field>
				<Field label="To"
					><input v-model="to" type="date" class="inp w-40" @change="load"
				/></Field>
				<Field label="Vehicle"
					><select v-model="vehicle" class="inp w-44" @change="load">
						<option value="">All vehicles</option>
						<option v-for="v in data?.vehicles" :key="v.name">{{ v.name }}</option>
					</select></Field
				>
				<a class="btn-secondary ml-auto" :href="reportLink" target="_blank"
					><i class="lucide-printer size-4" />Print / PDF</a
				>
			</div>
			<div class="card overflow-x-auto">
				<table class="tbl">
					<thead>
						<tr>
							<th>Date</th>
							<th>Voucher</th>
							<th>Vehicle</th>
							<th>Slip</th>
							<th>Item</th>
							<th class="!text-right">Qty</th>
							<th class="!text-right">Rate</th>
							<th class="!text-right">Debit</th>
							<th class="!text-right">Credit</th>
							<th class="!text-right">Balance</th>
						</tr>
					</thead>
					<tbody>
						<tr
							v-for="(r, i) in data?.statement || []"
							:key="i"
							:class="!r.voucher ? 'bg-slate-50 font-semibold' : ''"
						>
							<td>{{ dateFmt(r.date) }}</td>
							<td class="text-[12px]">{{ r.voucher || r.item_code }}</td>
							<td>{{ r.vehicle || "" }}</td>
							<td>{{ r.slip_no || "" }}</td>
							<td>{{ r.voucher ? r.item_code || r.voucher_type : "" }}</td>
							<td class="r">{{ r.qty ? num(r.qty) : "" }}</td>
							<td class="r">{{ r.rate ? num(r.rate) : "" }}</td>
							<td class="r">{{ r.debit ? num(r.debit) : "" }}</td>
							<td class="r text-green-700">{{ r.credit ? num(r.credit) : "" }}</td>
							<td class="r font-semibold">{{ num(r.balance) }}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>

		<div v-else-if="tab === 'Vehicles'">
			<div class="mb-3 flex justify-end">
				<button
					class="btn-secondary"
					@click="
						editV = {
							vehicle_no: '',
							vehicle_type: 'Truck',
							fuel_item: 'HSD',
							is_active: 1,
						}
					"
				>
					<i class="lucide-plus size-4" />Add vehicle
				</button>
			</div>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
				<div v-for="v in data?.vehicles" :key="v.name" class="card card-pad">
					<div class="flex items-center justify-between">
						<span class="text-[15px] font-semibold tracking-wide">{{ v.name }}</span
						><StatusPill :status="v.is_active ? 'Active' : 'Inactive'" />
					</div>
					<div class="mt-1 text-[12px] text-ink-2">
						{{ v.vehicle_type }} ·
						<FuelChip v-if="v.fuel_item" :item="v.fuel_item" size="xs" /> ·
						{{ v.driver_name || "No driver" }}
					</div>
					<button
						class="mt-2 text-[12px] text-brand-600 hover:underline"
						@click="editV = { ...v, vehicle_no: v.name }"
					>
						Edit
					</button>
				</div>
			</div>
		</div>

		<div v-else-if="tab === 'Invoices'" class="card overflow-x-auto">
			<table class="tbl">
				<thead>
					<tr>
						<th>Invoice</th>
						<th>Date</th>
						<th>Shift</th>
						<th class="!text-right">Amount</th>
						<th class="!text-right">Outstanding</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="r in data?.invoices" :key="r.name">
						<td>
							<a
								:href="deskUrl('Sales Invoice', r.name)"
								target="_blank"
								class="text-brand-600"
								>{{ r.name }}</a
							>
						</td>
						<td>{{ dateFmt(r.posting_date) }}</td>
						<td>{{ r.shift_sale_entry }}</td>
						<td class="r">{{ inr(r.grand_total) }}</td>
						<td
							class="r"
							:class="
								r.outstanding_amount > 0
									? 'font-semibold text-amber-700'
									: 'text-green-700'
							"
						>
							{{ inr(r.outstanding_amount) }}
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-else class="card overflow-x-auto">
			<table class="tbl">
				<thead>
					<tr>
						<th>Payment</th>
						<th>Date</th>
						<th>Mode</th>
						<th>Reference</th>
						<th class="!text-right">Amount</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="r in data?.payments" :key="r.name">
						<td>
							<a
								:href="deskUrl('Payment Entry', r.name)"
								target="_blank"
								class="text-brand-600"
								>{{ r.name }}</a
							>
						</td>
						<td>{{ dateFmt(r.posting_date) }}</td>
						<td>{{ r.mode_of_payment }}</td>
						<td>{{ r.reference_no }}</td>
						<td class="r">{{ inr(r.paid_amount) }}</td>
					</tr>
				</tbody>
			</table>
			<EmptyState v-if="!data?.payments?.length" title="No payments yet" />
		</div>

		<Modal
			:model-value="!!editV"
			:title="editV?.name ? 'Edit vehicle' : 'Add vehicle'"
			@update:model-value="editV = null"
		>
			<div v-if="editV" class="grid grid-cols-2 gap-3">
				<Field label="Vehicle no" required class="col-span-2"
					><input
						v-model="editV.vehicle_no"
						class="inp uppercase"
						:disabled="!!editV.name"
						placeholder="HR38AB4521"
				/></Field>
				<Field label="Type"
					><select v-model="editV.vehicle_type" class="inp">
						<option v-for="t in vtypes" :key="t">{{ t }}</option>
					</select></Field
				>
				<Field label="Default fuel"
					><select v-model="editV.fuel_item" class="inp">
						<option v-for="f in session.boot.fuels" :key="f.name">{{ f.name }}</option>
					</select></Field
				>
				<Field label="Driver"><input v-model="editV.driver_name" class="inp" /></Field>
				<Field label="Driver mobile"
					><input v-model="editV.driver_mobile" class="inp" inputmode="tel"
				/></Field>
				<Field label="Monthly limit (L)"
					><NumInput v-model="editV.monthly_limit_liters"
				/></Field>
				<label class="flex items-end gap-2 pb-2 text-[13px]"
					><input
						v-model="editV.is_active"
						type="checkbox"
						:true-value="1"
						:false-value="0"
					/>Active</label
				>
			</div>
			<template #footer
				><button class="btn-secondary" @click="editV = null">Close</button
				><button class="btn-primary" :disabled="!editV?.vehicle_no" @click="saveVehicle">
					Save
				</button></template
			>
		</Modal>
		<ReceivePayment v-model="payOpen" :fixed="customer" @done="load" />
	</div>
</template>
<script setup>
import { ref, computed, onMounted } from "vue";
import { toast } from "frappe-ui";
import { api, errorText, deskUrl } from "../api";
import { session, can } from "../session";
import { inr, num, dateFmt, today, addDays } from "../format";
import PageHeader from "../components/PageHeader.vue";
import KpiCard from "../components/KpiCard.vue";
import Field from "../components/Field.vue";
import NumInput from "../components/NumInput.vue";
import StatusPill from "../components/StatusPill.vue";
import FuelChip from "../components/FuelChip.vue";
import EmptyState from "../components/EmptyState.vue";
import Modal from "../components/Modal.vue";
import ReceivePayment from "../components/ReceivePayment.vue";

const props = defineProps({ customer: String });
const tabs = ["Statement", "Vehicles", "Invoices", "Payments"];
const vtypes = [
	"Truck",
	"Bus",
	"Car",
	"Tractor",
	"Tanker",
	"Two Wheeler",
	"Three Wheeler",
	"Generator / DG Set",
	"Other",
];
const tab = ref("Statement");
const data = ref(null);
const from = ref(addDays(today(), -30));
const to = ref(today());
const vehicle = ref("");
const payOpen = ref(false);
const editV = ref(null);
const s = computed(() => data.value?.summary || {});
const reportLink = computed(
	() =>
		`/desk/query-report/Credit Customer Statement?company=${encodeURIComponent(
			session.boot.station?.company || ""
		)}&customer=${encodeURIComponent(props.customer)}&from_date=${from.value}&to_date=${
			to.value
		}`
);
async function load() {
	data.value = await api("customer_detail", {
		customer: props.customer,
		from_date: from.value,
		to_date: to.value,
		vehicle: vehicle.value || null,
	});
}
async function saveVehicle() {
	try {
		await api("save_vehicle", { vehicle: { ...editV.value, customer: props.customer } });
		toast.success("Vehicle saved");
		editV.value = null;
		load();
	} catch (e) {
		toast.error(errorText(e));
	}
}
onMounted(load);
</script>
