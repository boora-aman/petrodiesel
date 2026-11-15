<template>
	<div>
		<PageHeader
			title="Fuel prices"
			subtitle="Daily retail selling prices (RSP), effective 06:00"
		>
			<template #actions
				><button v-if="canEdit && !editing" class="btn-primary" @click="startNew">
					<i class="lucide-plus size-4" />Update prices
				</button></template
			>
		</PageHeader>

		<div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
			<div
				v-for="p in session.boot.fuels"
				:key="p.name"
				class="card card-pad flex items-center justify-between"
			>
				<div>
					<FuelChip :item="p.name" />
					<div class="mt-1 text-[12px] text-ink-2">{{ p.item_name }}</div>
				</div>
				<div class="text-right">
					<div class="num text-[22px] font-semibold">
						{{ inr(current[p.name] ?? p.rate) }}
					</div>
					<div class="text-[11px] text-ink-3">per litre today</div>
				</div>
			</div>
		</div>

		<Section v-if="editing" title="New price update" class="mb-4">
			<div class="mb-3 grid grid-cols-2 gap-3 md:grid-cols-4">
				<Field label="Effective date"
					><input
						v-model="draft.effective_date"
						type="date"
						class="inp"
						@change="refreshOld"
				/></Field>
				<Field label="Effective from"
					><input v-model="draft.effective_time" type="time" step="60" class="inp"
				/></Field>
				<Field label="Source"
					><select v-model="draft.source" class="inp">
						<option>OMC SMS</option>
						<option>OMC Portal / App</option>
						<option>Email</option>
						<option>Manual</option>
					</select></Field
				>
			</div>
			<div class="divide-y divide-line rounded-lg border border-line">
				<div
					v-for="r in draft.items"
					:key="r.fuel_item"
					class="grid grid-cols-2 items-end gap-3 p-3 md:grid-cols-5"
				>
					<div class="col-span-2 md:col-span-1"><FuelChip :item="r.fuel_item" /></div>
					<AutoField label="Old price" :value="inr(r.old_price)" />
					<Field label="New price"><NumInput v-model="r.new_price" big /></Field>
					<AutoField
						label="Change"
						:value="
							(r.new_price - r.old_price >= 0 ? '+' : '') +
							num(r.new_price - r.old_price)
						"
						:tone="r.new_price > r.old_price ? 'bad' : 'good'"
					/>
					<AutoField
						label="Change %"
						:value="
							r.old_price
								? num(((r.new_price - r.old_price) * 100) / r.old_price) + '%'
								: '—'
						"
					/>
				</div>
			</div>
			<div class="mt-3 flex justify-end gap-2">
				<button class="btn-secondary" @click="editing = false">Cancel</button>
				<button
					class="btn-primary"
					:disabled="
						busy || draft.items.some((r) => !(r.new_price > 0)) || !changed.length
					"
					:title="changed.length ? '' : 'No price changed yet'"
					@click="submit"
				>
					<i class="lucide-check size-4" />Submit prices
				</button>
			</div>
		</Section>

		<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
			<Section title="Price trend" subtitle="Last 60 days" class="lg:col-span-2">
				<Chart
					v-if="chart"
					type="line"
					:labels="chart.labels"
					:datasets="chart.datasets"
					unit="₹"
					:height="280"
				/>
			</Section>
			<Section title="Past updates" flush>
				<div class="max-h-96 divide-y divide-line overflow-y-auto">
					<div
						v-for="u in history"
						:key="u.name + u.fuel_item"
						class="flex items-center justify-between px-4 py-2 text-[12px]"
					>
						<span
							>{{ dateFmt(u.effective_date) }}
							<FuelChip :item="u.fuel_item" size="xs"
						/></span>
						<span class="num whitespace-nowrap"
							><b>{{ inr(u.new_price) }}</b>
							<span
								class="ml-1.5 inline-block min-w-[52px] text-right text-[12px]"
								:class="
									u.change_amount > 0
										? 'text-red-600'
										: u.change_amount < 0
										? 'text-green-700'
										: 'text-ink-3'
								"
								>{{ u.change_amount > 0 ? "▲" : u.change_amount < 0 ? "▼" : "" }}
								{{
									u.change_amount ? num(Math.abs(u.change_amount)) : "no change"
								}}</span
							></span
						>
					</div>
				</div>
			</Section>
		</div>
	</div>
</template>
<script setup>
import { ref, computed, onMounted } from "vue";
import { toast } from "frappe-ui";
import { api, errorText } from "../api";
import { session, can, loadBoot } from "../session";
import { inr, num, dateFmt, today, addDays } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
import AutoField from "../components/AutoField.vue";
import NumInput from "../components/NumInput.vue";
import FuelChip from "../components/FuelChip.vue";
import Chart from "../components/charts/Chart.vue";

const canEdit = can("Fuel Price Update", "create");
const editing = ref(false);
const busy = ref(false);
const history = ref([]);
const chart = ref(null);
const current = ref({});
const draft = ref(null);

async function loadHistory() {
	const r = await api("frappe.desk.query_report.run", {
		report_name: "Fuel Price History",
		filters: { from_date: addDays(today(), -60), to_date: addDays(today(), 30) },
	});
	history.value = (r.result || []).filter((x) => x && x.name).reverse();
	chart.value = r.chart?.data || null;
}
async function refreshOld() {
	const items = await api(
		"petrodiesel.petrodiesel.doctype.fuel_price_update.fuel_price_update.get_fuel_items",
		{ effective_date: draft.value.effective_date }
	);
	draft.value.items = items.map((i) => ({
		...i,
		new_price:
			draft.value.items?.find((x) => x.fuel_item === i.fuel_item)?.new_price || i.old_price,
	}));
}
async function startNew() {
	draft.value = {
		doctype: "Fuel Price Update",
		effective_date: today(),
		effective_time: "06:00:00",
		source: "OMC SMS",
		items: [],
	};
	await refreshOld();
	editing.value = true;
}
const changed = computed(() =>
	(draft.value?.items || []).filter(
		(r) => Math.abs(Number(r.new_price) - Number(r.old_price)) >= 0.005
	)
);
async function submit() {
	if (busy.value || !changed.value.length) return;
	const lines = changed.value
		.map((r) => `${r.fuel_item}: ${r.old_price} → ${r.new_price}`)
		.join("\n");
	if (!window.confirm(`Submit new prices from ${draft.value.effective_date}?\n\n${lines}`))
		return;
	busy.value = true;
	try {
		const pl = await api("frappe.client.get_single_value", {
			doctype: "Petrodiesel Settings",
			field: "fuel_price_list",
		});
		await api("save_doc", {
			doc: {
				...draft.value,
				price_list: pl,
				items: changed.value.map(({ fuel_item, new_price }) => ({
					fuel_item,
					new_price,
				})),
			},
			action: "submit",
		});
		toast.success("Prices updated");
		editing.value = false;
		await loadBoot();
		await loadHistory();
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
}
onMounted(loadHistory);
</script>
