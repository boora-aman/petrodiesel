<template>
	<div>
		<PageHeader
			title="Outlet setup"
			subtitle="Outlet, tanks, dispensing units, shifts and settings"
		>
			<template #actions
				><a href="/desk/petrodiesel/petrol-pump" class="btn-secondary"
					><i class="lucide-external-link size-4" />Masters in Desk</a
				></template
			>
		</PageHeader>
		<div class="no-scrollbar mb-4 flex gap-1 overflow-x-auto border-b border-line">
			<button
				v-for="t in tabs"
				:key="t"
				class="tab-btn"
				:class="{ active: tab === t }"
				@click="tab = t"
			>
				{{ t }}
			</button>
		</div>
		<div v-if="!data"><Skeleton class="h-48 w-full" /></div>
		<template v-else>
			<!-- Outlet -->
			<div v-if="tab === 'Outlet'" class="grid grid-cols-1 gap-4 lg:grid-cols-3">
				<Section title="Outlet profile" class="lg:col-span-2">
					<div class="grid grid-cols-2 gap-3 md:grid-cols-3">
						<AutoField label="Name" :value="st.station_name" /><AutoField
							label="Oil company"
							:value="st.omc"
						/><AutoField label="RO code" :value="st.ro_code" />
						<AutoField label="Dealer" :value="st.dealer_name" /><AutoField
							label="GSTIN"
							:value="st.gstin || '—'"
						/><AutoField label="Company" :value="st.company" />
						<AutoField
							label="Walk-in customer"
							:value="st.walk_in_customer"
						/><AutoField label="Cash account" :value="st.cash_account" /><AutoField
							label="Short/excess account"
							:value="st.cash_short_excess_account"
						/>
					</div>
					<p class="mt-3 text-[12px] text-ink-3">{{ st.address }}</p>
					<a
						:href="deskUrl('Fuel Station', st.name)"
						class="mt-3 inline-flex text-[13px] text-brand-600 hover:underline"
						>Edit outlet in Desk →</a
					>
				</Section>
				<Section title="Licences" flush>
					<div class="divide-y divide-line">
						<div
							v-for="l in st.licences"
							:key="l.name"
							class="flex items-center justify-between px-4 py-2.5"
						>
							<div>
								<div class="text-[13px] font-medium">{{ l.licence_type }}</div>
								<div class="text-[11px] text-ink-3">{{ l.licence_no }}</div>
							</div>
							<ExpiryChip :date="l.valid_till" />
						</div>
					</div>
				</Section>
			</div>

			<!-- Tanks -->
			<div v-else-if="tab === 'Tanks'" class="grid grid-cols-1 gap-4 md:grid-cols-2">
				<Section
					v-for="t in data.tanks"
					:key="t.name"
					:title="t.name"
					:subtitle="t.warehouse"
				>
					<template #actions
						><FuelChip :item="t.fuel_item" /><StatusPill :status="t.status"
					/></template>
					<div class="grid grid-cols-3 gap-2">
						<AutoField
							label="Capacity"
							:value="litres(t.capacity_liters, 0)"
						/><AutoField label="Dead stock" :value="litres(t.dead_stock_liters, 0)" />
						<AutoField label="Safe fill" :value="t.safe_fill_percent + '%'" />
					</div>
					<div class="mt-3 flex items-center justify-between text-[12px]">
						<span class="text-ink-2">Calibration due</span
						><ExpiryChip :date="t.next_calibration_due" />
					</div>
					<div
						class="mt-3 text-[11px] font-semibold uppercase tracking-wider text-ink-3"
					>
						Calibration curve ({{ t.chart.length }} points)
					</div>
					<svg
						viewBox="0 0 300 100"
						class="mt-1 h-24 w-full rounded bg-slate-50"
						preserveAspectRatio="none"
					>
						<polyline
							fill="none"
							stroke="#0F766E"
							stroke-width="2"
							vector-effect="non-scaling-stroke"
							:points="curve(t)"
						/>
					</svg>
					<a
						:href="deskUrl('Fuel Tank Master', t.name)"
						class="mt-2 inline-flex text-[12px] text-brand-600 hover:underline"
						>Edit tank & chart in Desk →</a
					>
				</Section>
			</div>

			<!-- DUs -->
			<div v-else-if="tab === 'Dispensing units'" class="space-y-4">
				<Section
					v-for="du in data.dispensing_units"
					:key="du.name"
					:title="du.name"
					:subtitle="`${du.make} ${du.model || ''} · SN ${du.serial_no || '—'}`"
				>
					<template #actions
						><span class="text-[12px] text-ink-2">W&M stamping</span
						><ExpiryChip :date="du.wm_valid_till"
					/></template>
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
						<div
							v-for="n in du.nozzles"
							:key="n.name"
							class="rounded-lg border border-line p-3"
						>
							<div class="flex items-center justify-between">
								<span class="text-[14px] font-semibold">{{ n.name }}</span
								><StatusPill :status="n.status" />
							</div>
							<div class="mt-1 flex items-center gap-2 text-[12px] text-ink-2">
								<FuelChip :item="n.fuel_item" size="xs" /> Side
								{{ n.side || "—" }} · {{ n.tank }}
							</div>
							<div class="mt-2 text-[12px]">
								Totalizer <b class="num">{{ num(n.last_reading) }}</b>
							</div>
							<div class="mt-2 flex flex-wrap gap-2">
								<button class="btn-secondary btn-sm" @click="openMeter(n)">
									Meter change
								</button>
								<button
									v-if="n.status === 'Active'"
									class="btn-secondary btn-sm !text-amber-700"
									@click="setStatus(n, 'Under Maintenance')"
								>
									Maintenance
								</button>
								<button
									v-else
									class="btn-secondary btn-sm !text-green-700"
									@click="setStatus(n, 'Active')"
								>
									Set active
								</button>
							</div>
						</div>
					</div>
				</Section>
			</div>

			<!-- Shifts -->
			<Section v-else-if="tab === 'Shifts'" title="Shifts" flush>
				<table class="tbl">
					<thead>
						<tr>
							<th>#</th>
							<th>Shift</th>
							<th>Start</th>
							<th>End</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="s in data.shifts" :key="s.name">
							<td>{{ s.sequence }}</td>
							<td class="font-medium">{{ s.name }}</td>
							<td>{{ timeFmt(s.start_time) }}</td>
							<td>{{ timeFmt(s.end_time) }}</td>
							<td><StatusPill :status="s.is_active ? 'Active' : 'Inactive'" /></td>
						</tr>
					</tbody>
				</table>
			</Section>

			<!-- Settings -->
			<Section v-else-if="tab === 'Settings'" title="Controls & tolerances">
				<div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
					<Field label="Density tolerance (kg/m³)" hint="MDG: ±3.0"
						><NumInput
							v-model="settings.density_tolerance"
							:disabled="!data.can_edit_settings"
					/></Field>
					<Field label="Pump test tolerance (ml per 5 L)" hint="Legal Metrology: ±15 ml"
						><NumInput
							v-model="settings.pump_test_tolerance_ml"
							:disabled="!data.can_edit_settings"
					/></Field>
					<Field
						label="Default permissible loss %"
						hint="Used when the fuel item has none"
						><NumInput
							v-model="settings.default_permissible_loss"
							:disabled="!data.can_edit_settings"
					/></Field>
					<Field
						label="Cash short/excess tolerance (₹)"
						hint="Remarks required above this"
						><NumInput
							v-model="settings.cash_variance_tolerance"
							:disabled="!data.can_edit_settings"
					/></Field>
					<Field label="Licence expiry alert (days)"
						><NumInput
							v-model="settings.expiry_alert_days"
							:disabled="!data.can_edit_settings"
					/></Field>
					<div />
					<Toggle
						v-model="settings.require_shift_approval"
						label="Shift closings need manager approval"
						:disabled="!data.can_edit_settings"
					/>
					<Toggle
						v-model="settings.post_dsr_stock_adjustment"
						label="Reconcile ERPNext stock to dip on DSR submit"
						:disabled="!data.can_edit_settings"
					/>
				</div>
				<div class="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
					<AutoField
						label="Fuel price list"
						:value="settings.fuel_price_list"
					/><AutoField
						label="Fuel VAT template"
						:value="settings.fuel_tax_template"
					/><AutoField label="Lube GST template" :value="settings.lube_tax_template" />
				</div>
				<div v-if="data.can_edit_settings" class="mt-4 flex justify-end">
					<button class="btn-primary" :disabled="busy" @click="saveSettings">
						Save settings
					</button>
				</div>
				<p v-else class="mt-3 text-[12px] text-ink-3">
					Only the owner can change settings.
				</p>
			</Section>

			<!-- Users -->
			<Section v-else-if="tab === 'Users'" title="Users & roles" flush>
				<template #actions
					><a href="/desk/user/new" class="btn-secondary btn-sm"
						><i class="lucide-user-plus size-3.5" />Invite user</a
					></template
				>
				<EmptyState v-if="!data.users.length" title="Only the owner can see users" />
				<div class="divide-y divide-line">
					<div
						v-for="u in data.users"
						:key="u.name"
						class="flex flex-wrap items-center gap-2 px-4 py-3"
					>
						<div class="min-w-0 flex-1">
							<div class="text-[13px] font-medium">{{ u.full_name }}</div>
							<div class="text-[11px] text-ink-3">
								{{ u.name }} {{ u.employee ? "· " + u.employee : "" }}
							</div>
						</div>
						<span
							v-for="r in u.roles"
							:key="r"
							class="pill border-brand-100 bg-brand-50 text-brand-700"
							>{{ r.replace("Pump ", "") }}</span
						>
						<a :href="deskUrl('User', u.name)" class="text-[12px] text-brand-600"
							>Edit</a
						>
					</div>
				</div>
			</Section>
		</template>

		<Modal v-model="meter.open" title="Nozzle meter change">
			<div class="space-y-3">
				<p class="text-[13px] text-ink-2">
					Use when the totalizer is replaced or reset. Do it between shifts: the old
					final reading must match the last closing.
				</p>
				<AutoField label="Nozzle" :value="meter.nozzle" />
				<Field label="Old meter final reading"><NumInput v-model="meter.old" /></Field>
				<Field label="New meter start reading"><NumInput v-model="meter.new" /></Field>
				<Field label="Reason"
					><select v-model="meter.reason" class="inp">
						<option>Meter Replaced</option>
						<option>Meter Repaired / Reset</option>
						<option>Pulser / CPU Card Replaced</option>
						<option>Correction</option>
					</select></Field
				>
				<Field label="Technician"><input v-model="meter.technician" class="inp" /></Field>
			</div>
			<template #footer
				><button class="btn-secondary" @click="meter.open = false">Close</button
				><button class="btn-primary" :disabled="busy" @click="saveMeter">
					Submit
				</button></template
			>
		</Modal>
	</div>
</template>
<script setup>
import { ref, reactive, computed, onMounted, h } from "vue";
import { toast } from "frappe-ui";
import { api, errorText, deskUrl } from "../api";
import { loadBoot } from "../session";
import { num, litres, timeFmt, dateFmt, today } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
import AutoField from "../components/AutoField.vue";
import NumInput from "../components/NumInput.vue";
import FuelChip from "../components/FuelChip.vue";
import StatusPill from "../components/StatusPill.vue";
import Skeleton from "../components/Skeleton.vue";
import EmptyState from "../components/EmptyState.vue";
import Modal from "../components/Modal.vue";
import Toggle from "../components/Toggle.vue";

const ExpiryChip = (p) => {
	if (!p.date) return h("span", { class: "text-[12px] text-ink-3" }, "—");
	const days = Math.round((new Date(p.date) - new Date(today())) / 86400000);
	const cls =
		days < 0
			? "border-red-200 bg-red-50 text-red-700"
			: days <= 30
			? "border-amber-200 bg-amber-50 text-amber-700"
			: "border-green-200 bg-green-50 text-green-700";
	return h(
		"span",
		{ class: ["pill", cls] },
		`${dateFmt(p.date)} · ${days < 0 ? "expired" : days + " d"}`
	);
};
ExpiryChip.props = ["date"];

const tabs = ["Outlet", "Tanks", "Dispensing units", "Shifts", "Settings", "Users"];
const tab = ref("Outlet");
const data = ref(null);
const busy = ref(false);
const settings = reactive({});
const meter = reactive({
	open: false,
	nozzle: "",
	old: 0,
	new: 0,
	reason: "Meter Replaced",
	technician: "",
});
const st = computed(() => data.value?.station || {});
function curve(t) {
	if (!t.chart.length) return "";
	const maxD = t.chart[t.chart.length - 1].dip_mm || 1,
		maxV = t.chart[t.chart.length - 1].volume_liters || 1;
	return t.chart
		.map((p) => `${(p.dip_mm / maxD) * 300},${100 - (p.volume_liters / maxV) * 96}`)
		.join(" ");
}
async function load() {
	data.value = await api("setup_data");
	Object.assign(settings, data.value.settings);
}
async function saveSettings() {
	busy.value = true;
	try {
		await api("save_settings", { values: settings });
		toast.success("Settings saved");
		await loadBoot();
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
}
async function setStatus(n, status) {
	try {
		await api("set_nozzle_status", { nozzle: n.name, status });
		toast.success(`${n.name}: ${status}`);
		load();
	} catch (e) {
		toast.error(errorText(e));
	}
}
function openMeter(n) {
	Object.assign(meter, {
		open: true,
		nozzle: n.name,
		old: n.last_reading,
		new: 0,
		technician: "",
	});
}
async function saveMeter() {
	busy.value = true;
	try {
		await api("save_doc", {
			doc: {
				doctype: "Nozzle Meter Change",
				nozzle: meter.nozzle,
				posting_date: today(),
				reason: meter.reason,
				old_meter_final_reading: meter.old,
				new_meter_start_reading: meter.new,
				technician: meter.technician,
			},
			action: "submit",
		});
		toast.success("Meter change recorded");
		meter.open = false;
		load();
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
}
onMounted(load);
</script>
