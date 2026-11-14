<template>
	<div>
		<PageHeader
			title="Credit customers"
			subtitle="Fleet and institutional accounts, limits and dues"
		>
			<template #actions
				><button
					v-if="can('Payment Entry', 'create')"
					class="btn-primary"
					@click="payOpen = true"
				>
					<i class="lucide-hand-coins size-4" />Receive payment
				</button></template
			>
		</PageHeader>
		<div class="mb-3 grid grid-cols-2 gap-2 md:grid-cols-4">
			<div class="card px-3 py-2">
				<div class="text-[11px] text-ink-3">Customers</div>
				<div class="num text-[16px] font-semibold">{{ rows.length }}</div>
			</div>
			<div class="card px-3 py-2">
				<div class="text-[11px] text-ink-3">Total outstanding</div>
				<div class="num text-[16px] font-semibold">{{ compactInr(total) }}</div>
			</div>
			<div class="card px-3 py-2">
				<div class="text-[11px] text-ink-3">Over 80% of limit</div>
				<div class="num text-[16px] font-semibold text-amber-600">
					{{ rows.filter((r) => r.used_pct >= 80).length }}
				</div>
			</div>
			<div class="card px-3 py-2">
				<div class="text-[11px] text-ink-3">Vehicles</div>
				<div class="num text-[16px] font-semibold">
					{{ rows.reduce((a, r) => a + r.vehicles, 0) }}
				</div>
			</div>
		</div>
		<input v-model="q" class="inp mb-3 max-w-sm" placeholder="Search customer…" />
		<div class="card overflow-hidden">
			<div v-if="loading" class="p-4"><Skeleton class="h-40 w-full" /></div>
			<template v-else>
				<div class="hidden overflow-x-auto md:block">
					<table class="tbl">
						<thead>
							<tr>
								<th>Customer</th>
								<th class="!text-right">Vehicles</th>
								<th class="!text-right">Credit limit</th>
								<th class="!text-right">Outstanding</th>
								<th>Limit used</th>
								<th>Last payment</th>
								<th class="!text-right">Oldest due</th>
							</tr>
						</thead>
						<tbody>
							<tr
								v-for="r in filtered"
								:key="r.name"
								class="cursor-pointer"
								@click="$router.push(`/credit/${encodeURIComponent(r.name)}`)"
							>
								<td class="font-medium">{{ r.name }}</td>
								<td class="r">{{ r.vehicles }}</td>
								<td class="r">{{ r.limit ? inr(r.limit, true) : "—" }}</td>
								<td class="r font-semibold">{{ inr(r.outstanding) }}</td>
								<td class="w-48"><Meter :pct="r.used_pct" /></td>
								<td>{{ dateFmt(r.last_payment) || "—" }}</td>
								<td class="r" :class="r.overdue_days > 15 ? 'text-red-600' : ''">
									{{ r.overdue_days }} d
								</td>
							</tr>
						</tbody>
					</table>
				</div>
				<div class="divide-y divide-line md:hidden">
					<RouterLink
						v-for="r in filtered"
						:key="r.name"
						:to="`/credit/${encodeURIComponent(r.name)}`"
						class="block px-4 py-3"
					>
						<div class="flex justify-between">
							<span class="font-medium">{{ r.name }}</span
							><span class="num font-semibold">{{ compactInr(r.outstanding) }}</span>
						</div>
						<Meter :pct="r.used_pct" class="mt-2" />
						<div class="mt-1 text-[11px] text-ink-3">
							{{ r.vehicles }} vehicles · limit {{ inr(r.limit, true) }}
						</div>
					</RouterLink>
				</div>
			</template>
		</div>
		<ReceivePayment v-model="payOpen" :customers="rows.map((r) => r.name)" @done="load" />
	</div>
</template>
<script setup>
import { ref, computed, onMounted, h } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api";
import { can } from "../session";
import { inr, compactInr, dateFmt } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Skeleton from "../components/Skeleton.vue";
import ReceivePayment from "../components/ReceivePayment.vue";

const Meter = (p) =>
	h("div", { class: "flex items-center gap-2" }, [
		h("div", { class: "h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100" }, [
			h("div", {
				class: [
					"h-full",
					p.pct >= 100 ? "bg-red-600" : p.pct >= 80 ? "bg-amber-500" : "bg-green-600",
				],
				style: { width: Math.min(p.pct, 100) + "%" },
			}),
		]),
		h(
			"span",
			{ class: "num w-10 text-right text-[11px] text-ink-2" },
			Math.round(p.pct) + "%"
		),
	]);
Meter.props = ["pct"];

const route = useRoute();
const rows = ref([]);
const loading = ref(true);
const q = ref("");
const payOpen = ref(!!route.query.pay);
const filtered = computed(() =>
	rows.value.filter((r) => !q.value || r.name.toLowerCase().includes(q.value.toLowerCase()))
);
const total = computed(() => rows.value.reduce((a, r) => a + r.outstanding, 0));
async function load() {
	loading.value = true;
	rows.value = await api("credit_customers");
	loading.value = false;
}
onMounted(load);
</script>
