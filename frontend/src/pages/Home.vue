<template>
	<div>
		<div class="mb-5 flex flex-wrap items-center gap-3">
			<div class="w-full min-w-0 sm:w-auto sm:flex-1">
				<h1 class="text-[20px] font-semibold tracking-tight sm:text-[22px] lg:text-[26px]">
					{{ greeting }}, {{ firstName }}
				</h1>
				<div class="mt-1 flex flex-wrap items-center gap-2 text-[13px] text-ink-2">
					<span
						v-if="liveShift"
						class="pill border-green-200 bg-green-50 text-green-700"
					>
						<span class="size-1.5 animate-pulse rounded-full bg-green-600" />{{
							liveShift.name
						}}
						shift · {{ liveShift.start }}–{{ liveShift.end }}
					</span>
					<span class="hidden sm:inline">{{ dateFmt(date) }}</span>
				</div>
			</div>
			<input
				v-model="date"
				type="date"
				class="inp flex-1 sm:w-40 sm:flex-none"
				@change="load"
			/>
			<button class="btn-secondary" title="Refresh" @click="load">
				<i class="lucide-refresh-cw size-4" :class="loading ? 'animate-spin' : ''" />
			</button>
		</div>

		<!-- Quick actions by role -->
		<div class="mb-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
			<RouterLink
				v-for="a in actions"
				:key="a.to"
				:to="a.to"
				class="card flex items-center gap-3 px-3 py-3 hover:border-brand-600 hover:bg-brand-50/40"
			>
				<span class="flex size-9 items-center justify-center rounded-lg bg-brand-50"
					><i :class="a.icon" class="size-5 text-brand-600"
				/></span>
				<span class="text-[13px] font-medium leading-4">{{ a.label }}</span>
			</RouterLink>
		</div>

		<!-- Prices -->
		<div class="mb-5 flex flex-wrap items-center gap-2">
			<span class="text-[12px] font-semibold uppercase tracking-wider text-ink-3"
				>Today's prices</span
			>
			<span
				v-for="p in data?.prices || []"
				:key="p.item"
				class="card flex items-center gap-2 px-3 py-1.5"
			>
				<FuelChip :item="p.item" size="xs" /><span class="num text-[14px] font-semibold">{{
					inr(p.rate)
				}}</span
				><span class="text-[11px] text-ink-3">/L</span>
			</span>
			<RouterLink
				v-if="can('Fuel Price Update', 'create')"
				to="/prices"
				class="btn-ghost btn-sm"
				>Update prices</RouterLink
			>
		</div>

		<!-- KPIs -->
		<div v-if="showMoney" class="mb-6 grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
			<KpiCard
				label="Fuel sale today"
				:loading="loading"
				:value="litres(k.fuel_today, 0)"
				:caption="`${date === today() ? 'So far · yesterday' : 'Day before'} ${litres(
					k.fuel_yesterday,
					0
				)}`"
				:badge="pct(k.fuel_today, k.fuel_yesterday)"
				:tone="date === today() || k.fuel_today >= k.fuel_yesterday ? 'good' : 'warn'"
				:spark="fuelSpark"
			/>
			<KpiCard
				label="Gross sales today"
				:loading="loading"
				:value="compactInr(k.gross_today)"
				:caption="`${date === today() ? 'So far · yesterday' : 'Day before'} ${compactInr(
					k.gross_yesterday
				)}`"
				:badge="pct(k.gross_today, k.gross_yesterday)"
				:tone="date === today() || k.gross_today >= k.gross_yesterday ? 'good' : 'warn'"
			/>
			<KpiCard
				label="Credit sales today"
				:loading="loading"
				:value="compactInr(k.credit_today)"
				caption="Billed to credit customers"
			/>
			<KpiCard
				label="Digital collection today"
				:loading="loading"
				:value="compactInr(k.digital_today)"
				caption="UPI · Card · Fleet cards"
			/>
			<KpiCard
				label="Cash short / excess today"
				:loading="loading"
				:value="signedInr(k.short_excess_today)"
				:tone="k.short_excess_today < -0.5 ? 'bad' : 'neutral'"
				:badge="
					k.short_excess_today < -0.5
						? 'Shortage'
						: k.short_excess_today > 0.5
						? 'Excess'
						: 'Tallied'
				"
				caption="All shifts today"
			/>
			<KpiCard
				label="Gross sales this month"
				:loading="loading"
				:value="compactInr(k.gross_month)"
			/>
			<KpiCard
				label="Fuel sale this month"
				:loading="loading"
				:value="litres(k.fuel_month, 0)"
			/>
			<KpiCard
				label="Fuel stock in tanks"
				:loading="loading"
				:value="litres(k.stock_total, 0)"
			/>
			<KpiCard
				label="Credit outstanding"
				:loading="loading"
				:value="compactInr(k.credit_outstanding)"
				caption="All credit customers"
			/>
			<KpiCard
				label="Stock gain / loss (month)"
				:loading="loading"
				:value="(k.variance_month > 0 ? '+' : '') + litres(k.variance_month, 0)"
				:tone="k.variance_month < 0 ? 'bad' : 'good'"
				caption="From Daily Stock Registers"
			/>
		</div>

		<!-- Tanks -->
		<div class="mb-3 flex items-center gap-2">
			<h2 class="h-section">Tanks</h2>
			<span class="text-[12px] text-ink-3">Book stock from ERPNext · last dip shown</span>
		</div>
		<div class="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
			<template v-if="loading && !data"
				><div v-for="i in 4" :key="i" class="card h-44 animate-pulse bg-slate-100"
			/></template>
			<TankGauge v-for="t in data?.tanks || []" :key="t.name" :tank="t" />
		</div>

		<div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
			<div class="space-y-4 xl:col-span-2">
				<Section
					v-if="showMoney"
					title="Daily fuel sales"
					subtitle="Litres per day by fuel, last 30 days"
				>
					<Chart
						type="bar"
						stacked
						:labels="data?.charts.daily_fuel.labels || []"
						:datasets="data?.charts.daily_fuel.datasets || []"
						unit="L"
						:loading="loading && !data"
						:height="280"
					/>
				</Section>
				<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
					<Section
						title="Machine-wise sales today"
						subtitle="Litres and value per machine side"
						flush
					>
						<EmptyState
							v-if="!(data?.machines || []).length"
							title="No shift closings today yet"
							icon="lucide-fuel"
						/>
						<div v-else class="overflow-x-auto">
							<table class="tbl">
								<thead>
									<tr>
										<th>Machine</th>
										<th>Attendants</th>
										<th class="!text-right">Sale (L)</th>
										<th class="!text-right">Value</th>
									</tr>
								</thead>
								<tbody>
									<tr
										v-for="m in data.machines"
										:key="m.dispensing_unit + m.side"
									>
										<td class="font-semibold">
											{{ m.dispensing_unit }}
											<span class="font-normal text-ink-3"
												>side {{ m.side || "—" }}</span
											>
										</td>
										<td class="wrap text-[12px] text-ink-2">
											{{ m.attendants || "—" }}
										</td>
										<td class="r">{{ num(m.sale_qty, 0) }}</td>
										<td class="r">{{ inr(m.sale_amount, true) }}</td>
									</tr>
								</tbody>
							</table>
						</div>
					</Section>
					<Section
						v-if="showMoney"
						title="Attendant collection today"
						subtitle="Cash due vs cash handed, per attendant"
						flush
					>
						<EmptyState
							v-if="!(data?.attendants || []).length"
							title="Nothing yet today"
							icon="lucide-users"
						/>
						<div v-else class="overflow-x-auto">
							<table class="tbl">
								<thead>
									<tr>
										<th>Attendant</th>
										<th class="!text-right">Cash due</th>
										<th class="!text-right">Handed</th>
										<th class="!text-right">Short/Excess</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="a in data.attendants" :key="a.attendant">
										<td class="font-medium">
											{{ a.attendant_name }}
											<div class="text-[11px] font-normal text-ink-3">
												{{ a.shifts }}
											</div>
										</td>
										<td class="r">{{ inr(a.expected_cash, true) }}</td>
										<td class="r">
											{{ a.cash_handed ? inr(a.cash_handed, true) : "—" }}
										</td>
										<td
											class="r font-semibold"
											:class="
												a.short_excess < -0.5
													? 'text-red-600'
													: 'text-green-700'
											"
										>
											{{ a.cash_handed ? signedInr(a.short_excess) : "—" }}
										</td>
									</tr>
								</tbody>
							</table>
						</div>
					</Section>
				</div>
				<div v-if="showMoney" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
					<Section
						title="Collection mix"
						subtitle="Cash, credit and digital, last 30 days"
					>
						<Chart
							type="donut"
							:labels="data?.charts.collection_mix.labels || []"
							:datasets="data?.charts.collection_mix.datasets || []"
							unit="₹"
							:loading="loading && !data"
							:height="260"
						/>
					</Section>
					<Section
						title="Daily stock gain / loss"
						subtitle="From the Daily Stock Register, litres"
					>
						<Chart
							type="line"
							:labels="data?.charts.variance.labels || []"
							:datasets="data?.charts.variance.datasets || []"
							unit="L"
							zero-line
							:loading="loading && !data"
							:height="260"
						/>
					</Section>
				</div>
				<Section
					v-if="showMoney && (data?.top_credit || []).length"
					title="Top credit dues"
					flush
				>
					<template #actions
						><RouterLink to="/credit" class="btn-ghost btn-sm"
							>All customers</RouterLink
						></template
					>
					<div class="divide-y divide-line">
						<RouterLink
							v-for="c in data.top_credit"
							:key="c.name"
							:to="`/credit/${encodeURIComponent(c.name)}`"
							class="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50"
						>
							<span class="min-w-0 flex-1 truncate text-[13px] font-medium">{{
								c.name
							}}</span>
							<div
								class="hidden h-1.5 w-32 overflow-hidden rounded-full bg-slate-100 sm:block"
							>
								<div
									class="h-full"
									:class="
										c.used_pct >= 100
											? 'bg-red-600'
											: c.used_pct >= 80
											? 'bg-amber-500'
											: 'bg-green-600'
									"
									:style="{ width: Math.min(c.used_pct, 100) + '%' }"
								/>
							</div>
							<span class="num w-28 text-right text-[13px] font-semibold">{{
								inr(c.outstanding, true)
							}}</span>
						</RouterLink>
					</div>
				</Section>
			</div>

			<div class="space-y-4">
				<Section title="Needs attention" flush>
					<template #actions
						><span class="pill border-red-200 bg-red-50 text-red-700">{{
							attention.length
						}}</span></template
					>
					<EmptyState
						v-if="!attention.length"
						title="All caught up"
						icon="lucide-circle-check"
					/>
					<div v-else class="max-h-[420px] divide-y divide-line overflow-y-auto">
						<RouterLink
							v-for="(a, i) in attention"
							:key="i"
							:to="linkFor(a)"
							class="flex gap-3 px-4 py-3 hover:bg-gray-50"
						>
							<i :class="iconFor(a)" class="mt-0.5 size-4 shrink-0" />
							<div class="min-w-0">
								<div class="text-[13px] font-medium">{{ a.title }}</div>
								<div v-if="a.detail" class="text-[12px] text-ink-2">
									{{ a.detail }}
								</div>
							</div>
						</RouterLink>
					</div>
				</Section>

				<Section title="Today's shifts" flush>
					<div class="divide-y divide-line">
						<div v-for="s in data?.shifts || []" :key="s.shift" class="px-4 py-3">
							<div class="flex items-center justify-between">
								<span class="text-[13px] font-semibold"
									>{{ s.shift }}
									<span class="font-normal text-ink-3"
										>{{ s.start_time }}–{{ s.end_time }}</span
									></span
								>
								<StatusPill v-if="!s.entries.length" status="Not started" />
							</div>
							<RouterLink
								v-for="e in s.entries"
								:key="e.name"
								:to="`/shifts/${e.name}`"
								class="mt-2 flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 hover:bg-slate-100"
							>
								<div class="min-w-0">
									<div class="truncate text-[12px] font-medium">
										{{ e.cashier_name || e.name }}
									</div>
									<div class="num text-[11px] text-ink-2">
										{{ litres(e.total_sale_qty, 0) }} ·
										<span
											:class="e.short_excess < -0.5 ? 'text-red-600' : ''"
											>{{ signedInr(e.short_excess) }}</span
										>
									</div>
								</div>
								<StatusPill
									:status="
										e.workflow_state || (e.docstatus ? 'Submitted' : 'Draft')
									"
								/>
							</RouterLink>
							<RouterLink
								v-if="
									!s.entries.length &&
									can('Shift Sale Entry', 'create') &&
									date === today()
								"
								:to="`/shifts/new?shift=${encodeURIComponent(s.shift)}`"
								class="mt-2 inline-flex text-[12px] font-medium text-brand-600 hover:underline"
								>Start closing →</RouterLink
							>
						</div>
					</div>
				</Section>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { toast } from "frappe-ui";
import { api, errorText } from "../api";
import { session, can } from "../session";
import { inr, num, litres, compactInr, signedInr, dateFmt, today, timeFmt } from "../format";
import KpiCard from "../components/KpiCard.vue";
import TankGauge from "../components/TankGauge.vue";
import Section from "../components/Section.vue";
import FuelChip from "../components/FuelChip.vue";
import StatusPill from "../components/StatusPill.vue";
import EmptyState from "../components/EmptyState.vue";
import Chart from "../components/charts/Chart.vue";

const data = ref(null);
const loading = ref(true);
const date = ref(today());
const k = computed(() => data.value?.kpis || {});
const view = computed(() => session.boot.view);
const showMoney = computed(() => view.value !== "stock");
const firstName = computed(() => (session.boot.full_name || "").split(" ")[0]);
const greeting = computed(() => {
	const h = new Date().getHours();
	return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
});
const attention = computed(() => data.value?.attention || []);
const fuelSpark = computed(() => {
	const d = data.value?.charts?.daily_fuel;
	if (!d) return [];
	return d.labels
		.map((_, i) => d.datasets.reduce((a, s) => a + (Number(s.values[i]) || 0), 0))
		.slice(-14);
});
const liveShift = computed(() => {
	const now = new Date().toTimeString().slice(0, 5);
	for (const s of session.boot.shifts || []) {
		const st = timeFmt(s.start_time),
			en = timeFmt(s.end_time);
		if ((st <= en && now >= st && now < en) || (st > en && (now >= st || now < en)))
			return { name: s.name, start: st, end: en };
	}
	return null;
});
const actions = computed(() =>
	[
		can("Shift Sale Entry", "create") && {
			label: "New shift closing",
			to: "/shifts/new",
			icon: "lucide-receipt-indian-rupee",
		},
		can("Tank Dip Reading", "create") && {
			label: "Tank dip reading",
			to: "/dips/new",
			icon: "lucide-ruler",
		},
		can("Tanker Receipt", "create") && {
			label: "Tanker receipt",
			to: "/tankers/new",
			icon: "lucide-truck",
		},
		can("Daily Stock Register", "create") && {
			label: "Daily stock register",
			to: "/dsr/new",
			icon: "lucide-notebook-tabs",
		},
		can("Pump Test Log", "create") && {
			label: "Pump test",
			to: "/pump-tests/new",
			icon: "lucide-flask-conical",
		},
		["owner", "manager"].includes(view.value) && {
			first: true,
			label: "Approvals",
			to: "/approvals",
			icon: "lucide-badge-check",
		},
	]
		.filter(Boolean)
		// managers always keep the Approvals shortcut among the four
		.sort((a, b) => (b.first ? 1 : 0) - (a.first ? 1 : 0))
		.slice(0, 4)
);

function pct(a, b) {
	// today is still running: a % against all of yesterday only alarms
	if (!b || date.value === today()) return "";
	const p = ((a - b) * 100) / b;
	return `${p >= 0 ? "+" : ""}${p.toFixed(1)}%`;
}
function linkFor(a) {
	const m = {
		shift: `/shifts/${a.name}`,
		tanker: `/tankers/${a.name}`,
		dsr: a.name ? `/dsr/new?date=${a.name}` : "/dsr/new",
		nozzle: "/setup",
		compliance: "/setup",
		stock: "/tankers/new",
		credit: `/credit/${encodeURIComponent(a.name)}`,
	};
	return m[a.type] || "/alerts";
}
function iconFor(a) {
	const base =
		{
			shift: "lucide-receipt-indian-rupee",
			tanker: "lucide-truck",
			dsr: "lucide-notebook-tabs",
			nozzle: "lucide-wrench",
			compliance: "lucide-shield-alert",
			stock: "lucide-fuel",
			credit: "lucide-credit-card",
		}[a.type] || "lucide-info";
	return [base, a.severity === "danger" ? "text-red-600" : "text-amber-600"];
}
async function load() {
	loading.value = true;
	try {
		data.value = await api("dashboard", { date: date.value });
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		loading.value = false;
	}
}
onMounted(load);
</script>
