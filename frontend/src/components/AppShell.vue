<template>
	<div class="min-h-screen bg-canvas">
		<!-- Sidebar (desktop) -->
		<aside
			class="hidden lg:flex fixed inset-y-0 left-0 z-30 flex-col border-r border-line bg-white transition-all"
			:class="collapsed ? 'w-16' : 'w-60'"
		>
			<div class="flex h-14 items-center gap-2.5 border-b border-line px-3">
				<img
					:src="'/assets/petrodiesel/images/logo.svg'"
					class="size-8 rounded-lg"
					alt=""
				/>
				<div v-if="!collapsed" class="min-w-0">
					<div class="text-[15px] font-semibold leading-4">PetroDesk</div>
					<div class="truncate text-[11px] text-ink-3">
						{{ boot.station?.station_name }}
					</div>
				</div>
			</div>
			<nav class="flex-1 overflow-y-auto px-2 py-3">
				<template v-for="group in navGroups" :key="group.label">
					<div
						v-if="!collapsed"
						class="px-2 pb-1 pt-3 text-[10px] font-semibold uppercase tracking-wider text-ink-3"
					>
						{{ group.label }}
					</div>
					<div v-else class="my-2 border-t border-line" />
					<RouterLink
						v-for="item in group.items"
						:key="item.to"
						:to="item.to"
						:title="item.label"
						class="group mb-0.5 flex h-9 items-center gap-2.5 rounded-lg px-2.5 text-[13px] font-medium text-ink-2 hover:bg-gray-100 hover:text-ink"
						:class="isActive(item) ? '!bg-brand-50 !text-brand-700' : ''"
					>
						<i :class="item.icon" class="size-4 shrink-0" />
						<span v-if="!collapsed" class="flex-1 truncate">{{ item.label }}</span>
						<span
							v-if="!collapsed && item.badge"
							class="rounded-full bg-red-600 px-1.5 text-[10px] font-semibold text-white"
						>
							{{ item.badge }}
						</span>
					</RouterLink>
				</template>
			</nav>
			<button
				class="flex h-10 items-center gap-2 border-t border-line px-5 text-[12px] text-ink-3 hover:text-ink"
				@click="collapsed = !collapsed"
			>
				<i
					:class="collapsed ? 'lucide-panel-left-open' : 'lucide-panel-left-close'"
					class="size-4"
				/>
				<span v-if="!collapsed">Collapse</span>
			</button>
		</aside>

		<!-- Main column -->
		<div :class="collapsed ? 'lg:pl-16' : 'lg:pl-60'" class="transition-all">
			<!-- Top bar -->
			<header class="sticky top-0 z-20 border-b border-line bg-white/95 backdrop-blur">
				<div class="mx-auto flex h-14 max-w-app items-center gap-3 px-4 lg:px-6">
					<img
						:src="'/assets/petrodiesel/images/logo.svg'"
						class="size-8 rounded-lg lg:hidden"
						alt=""
					/>
					<div class="min-w-0 lg:hidden">
						<div class="truncate text-[14px] font-semibold leading-4">
							{{ boot.station?.station_name }}
						</div>
						<div class="text-[11px] text-ink-3">
							{{ boot.station?.omc }} · {{ boot.station?.ro_code }}
						</div>
					</div>
					<div class="hidden min-w-0 items-center gap-2 lg:flex">
						<span
							class="pill shrink-0 whitespace-nowrap border-brand-100 bg-brand-50 text-brand-700"
							>{{ boot.station?.omc }} {{ boot.station?.ro_code }}</span
						>
						<span
							class="hidden truncate text-[13px] text-ink-2 2xl:inline"
							:title="boot.station?.address"
							>{{ boot.station?.address }}</span
						>
					</div>

					<div class="relative ml-auto hidden w-56 md:block xl:w-60 2xl:w-72">
						<i
							class="lucide-search absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-3"
						/>
						<input
							v-model="q"
							class="inp h-9 pl-9"
							placeholder="Search vehicle, customer, document…"
							@input="doSearch"
							@focus="showSearch = true"
							@blur="hideSearchSoon"
						/>
						<div
							v-if="showSearch && results.length"
							class="absolute left-0 right-0 top-11 z-40 overflow-hidden rounded-lg border border-line bg-white shadow-lg"
						>
							<button
								v-for="r in results"
								:key="r.doctype + r.name"
								class="flex w-full items-center justify-between px-3 py-2 text-left text-[13px] hover:bg-gray-50"
								@mousedown.prevent="openResult(r)"
							>
								<span class="font-medium">{{ r.label }}</span>
								<span class="text-[11px] text-ink-3"
									>{{ r.type }}
									{{
										r.description && r.description !== r.type
											? "· " + r.description
											: ""
									}}</span
								>
							</button>
						</div>
					</div>

					<div class="hidden shrink-0 items-center gap-3 xl:flex">
						<span
							v-for="f in boot.fuels"
							:key="f.name"
							class="num inline-flex items-center gap-1 whitespace-nowrap text-[12px] text-ink-2"
						>
							<FuelChip :item="f.name" size="xs" /> {{ inr(f.rate) }}
						</span>
					</div>

					<RouterLink
						to="/alerts"
						class="relative ml-auto rounded-lg p-2 hover:bg-gray-100 md:ml-0"
						title="Alerts"
					>
						<i class="lucide-bell size-5 text-ink-2" />
						<span
							v-if="alertCount"
							class="absolute right-1 top-1 size-2 rounded-full bg-red-600"
						/>
					</RouterLink>

					<div class="relative">
						<button
							class="flex items-center gap-2 rounded-lg p-1 hover:bg-gray-100"
							@click="menuOpen = !menuOpen"
						>
							<span
								class="flex size-8 items-center justify-center rounded-full bg-brand-600 text-[12px] font-semibold text-white"
								>{{ initials }}</span
							>
							<span class="hidden max-w-[140px] text-left md:block">
								<span
									class="block truncate whitespace-nowrap text-[13px] font-medium leading-4"
									>{{ boot.full_name }}</span
								>
								<span class="block text-[11px] capitalize text-ink-3">{{
									roleLabel
								}}</span>
							</span>
						</button>
						<div
							v-if="menuOpen"
							class="absolute right-0 top-11 z-40 w-56 overflow-hidden rounded-lg border border-line bg-white py-1 shadow-lg"
							@mouseleave="menuOpen = false"
						>
							<div class="border-b border-line px-3 py-2">
								<div class="text-[13px] font-medium">{{ boot.full_name }}</div>
								<div class="text-[11px] text-ink-3">{{ boot.user }}</div>
							</div>
							<a
								href="/assets/petrodiesel/docs/PetroDesk-User-Guide.pdf"
								target="_blank"
								class="flex items-center gap-2 px-3 py-2 text-[13px] hover:bg-gray-50"
								><i class="lucide-book-open size-4" /> User guide (PDF)</a
							>
							<a
								href="/desk"
								class="flex items-center gap-2 px-3 py-2 text-[13px] hover:bg-gray-50"
								><i class="lucide-layout-grid size-4" /> Open ERPNext Desk</a
							>
							<button
								class="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-red-600 hover:bg-red-50"
								@click="logout"
							>
								<i class="lucide-log-out size-4" /> Log out
							</button>
						</div>
					</div>
				</div>
			</header>

			<main class="mx-auto max-w-app px-4 pb-28 pt-4 lg:px-6 lg:pb-24 lg:pt-6">
				<slot />
			</main>
		</div>

		<!-- Bottom nav (mobile/tablet) -->
		<nav
			class="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-white pb-[env(safe-area-inset-bottom)] lg:hidden"
		>
			<div class="grid grid-cols-5">
				<RouterLink
					v-for="item in bottomNav"
					:key="item.to"
					:to="item.to"
					class="relative flex h-14 flex-col items-center justify-center gap-0.5 text-[10px] font-medium text-ink-3"
					:class="isActive(item) ? '!text-brand-600' : ''"
				>
					<i :class="item.icon" class="size-5" />
					{{ item.label }}
					<span
						v-if="item.badge"
						class="absolute right-[28%] top-1.5 rounded-full bg-red-600 px-1 text-[9px] text-white"
						>{{ item.badge }}</span
					>
				</RouterLink>
			</div>
		</nav>

		<!-- Quick actions -->
		<button
			v-if="quickActions.length && showFab"
			class="fixed bottom-20 right-4 z-30 flex size-14 items-center justify-center rounded-full bg-brand-600 text-white shadow-lg hover:bg-brand-700 lg:bottom-6 lg:right-6"
			title="Quick actions"
			@click="fabOpen = !fabOpen"
		>
			<i :class="fabOpen ? 'lucide-x' : 'lucide-plus'" class="size-6" />
		</button>
		<div v-if="fabOpen" class="fixed inset-0 z-20 bg-slate-900/30" @click="fabOpen = false" />
		<div
			v-if="fabOpen"
			class="fixed bottom-36 right-4 z-30 w-60 overflow-hidden rounded-lg border border-line bg-white shadow-xl lg:bottom-24 lg:right-6"
		>
			<RouterLink
				v-for="a in quickActions"
				:key="a.to"
				:to="a.to"
				class="flex items-center gap-3 px-4 py-3 text-[14px] font-medium hover:bg-gray-50"
				@click="fabOpen = false"
			>
				<i :class="a.icon" class="size-5 text-brand-600" /> {{ a.label }}
			</RouterLink>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from "vue";
import { useRoute, useRouter } from "vue-router";
import { session, logout, can, refreshCounts } from "../session";
import { api } from "../api";
import { inr } from "../format";
import FuelChip from "./FuelChip.vue";

const route = useRoute();
const router = useRouter();
const boot = computed(() => session.boot || {});
const collapsed = ref(localStorage.getItem("pd-collapsed") === "1");
const menuOpen = ref(false);
const fabOpen = ref(false);
const q = ref("");
const results = ref([]);
const showSearch = ref(false);
let timer = null;

const pending = computed(
	() => (boot.value.counts?.pending_shifts || 0) + (boot.value.counts?.pending_tankers || 0)
);
const alertCount = computed(() => boot.value.counts?.unread || 0);
const isManager = computed(() => ["owner", "manager"].includes(boot.value.view));
const initials = computed(() =>
	(boot.value.full_name || "?")
		.split(" ")
		.map((p) => p[0])
		.slice(0, 2)
		.join("")
		.toUpperCase()
);
const roleLabel = computed(
	() =>
		({ owner: "Owner", manager: "Manager", cashier: "Cashier", stock: "Stock Keeper" }[
			boot.value.view
		] || "User")
);

const navGroups = computed(() => {
	const g = [
		{
			label: "Operations",
			items: [
				{ label: "Home", to: "/", icon: "lucide-house", exact: true },
				boot.value.view !== "stock" &&
					can("Shift Sale Entry", "read") && {
						label: "Shift Closing",
						to: "/shifts",
						icon: "lucide-receipt-indian-rupee",
					},
				can("Tanker Receipt", "read") && {
					label: "Tanker Receipts",
					to: "/tankers",
					icon: "lucide-truck",
				},
				can("Tank Dip Reading", "read") && {
					label: "Tank Dips",
					to: "/dips",
					icon: "lucide-ruler",
				},
				can("Daily Stock Register", "read") && {
					label: "Daily Stock Register",
					to: "/dsr",
					icon: "lucide-notebook-tabs",
				},
				can("Pump Test Log", "read") && {
					label: "Pump Tests",
					to: "/pump-tests",
					icon: "lucide-flask-conical",
				},
			],
		},
		{
			label: "Stock",
			items: [
				can("Shop Purchase", "read") && {
					label: "Shop Purchases",
					to: "/purchases",
					icon: "lucide-shopping-cart",
				},
				can("Internal Stock Transfer", "read") && {
					label: "Stock Transfers",
					to: "/transfers",
					icon: "lucide-arrow-left-right",
				},
			],
		},
		{
			label: "Commercial",
			items: [
				can("Fuel Price Update", "read") && {
					label: "Price Updates",
					to: "/prices",
					icon: "lucide-tag",
				},
				boot.value.view !== "stock" &&
					can("Customer", "read") && {
						label: "Credit Customers",
						to: "/credit",
						icon: "lucide-users",
					},
				boot.value.view !== "stock" &&
					can("Credit Bill", "read") && {
						label: "Credit Bills",
						to: "/credit-bills",
						icon: "lucide-file-text",
					},
				boot.value.view !== "stock" &&
					can("Staff Advance", "read") && {
						label: "Staff Advances",
						to: "/advances",
						icon: "lucide-hand-coins",
					},
				{ label: "Reports", to: "/reports", icon: "lucide-chart-column" },
			],
		},
		isManager.value && {
			label: "Workflow",
			items: [
				{
					label: "Approvals",
					to: "/approvals",
					icon: "lucide-badge-check",
					badge: pending.value || null,
				},
				{ label: "Alerts", to: "/alerts", icon: "lucide-bell" },
			],
		},
		isManager.value && {
			label: "Setup",
			items: [{ label: "Outlet Setup", to: "/setup", icon: "lucide-settings" }],
		},
	];
	return g
		.filter(Boolean)
		.map((x) => ({ ...x, items: x.items.filter(Boolean) }))
		.filter((x) => x.items.length);
});

const bottomNav = computed(() => {
	const v = boot.value.view;
	const items = [{ label: "Home", to: "/", icon: "lucide-house", exact: true }];
	if (v === "stock") {
		items.push({ label: "Dips", to: "/dips", icon: "lucide-ruler" });
		items.push({ label: "Tankers", to: "/tankers", icon: "lucide-truck" });
		items.push({ label: "DSR", to: "/dsr", icon: "lucide-notebook-tabs" });
	} else {
		items.push({ label: "Shifts", to: "/shifts", icon: "lucide-receipt-indian-rupee" });
		items.push({
			label: "Stock",
			to: v === "cashier" ? "/dips" : "/dsr",
			icon: "lucide-fuel",
		});
		if (isManager.value)
			items.push({
				label: "Approvals",
				to: "/approvals",
				icon: "lucide-badge-check",
				badge: pending.value || null,
			});
		else items.push({ label: "Credit", to: "/credit", icon: "lucide-users" });
	}
	items.push({ label: "More", to: "/more", icon: "lucide-menu" });
	return items;
});

const quickActions = computed(() =>
	[
		can("Shift Sale Entry", "create") && {
			label: "New Shift Closing",
			to: "/shifts/new",
			icon: "lucide-receipt-indian-rupee",
		},
		can("Tank Dip Reading", "create") && {
			label: "Dip Reading",
			to: "/dips/new",
			icon: "lucide-ruler",
		},
		can("Tanker Receipt", "create") && {
			label: "Tanker Receipt",
			to: "/tankers/new",
			icon: "lucide-truck",
		},
		can("Pump Test Log", "create") && {
			label: "Pump Test",
			to: "/pump-tests/new",
			icon: "lucide-flask-conical",
		},
		can("Payment Entry", "create") && {
			label: "Receive Payment",
			to: "/credit?pay=1",
			icon: "lucide-hand-coins",
		},
	].filter(Boolean)
);

const showFab = computed(
	() =>
		!/New$/.test(String(route.name)) &&
		!route.params.name &&
		!["Customer", "Report"].includes(route.name)
);

function isActive(item) {
	if (item.exact) return route.path === item.to;
	return route.path === item.to || route.path.startsWith(item.to + "/");
}

function doSearch() {
	clearTimeout(timer);
	timer = setTimeout(async () => {
		results.value = q.value.length >= 2 ? await api("search", { q: q.value }) : [];
	}, 250);
}
function hideSearchSoon() {
	setTimeout(() => (showSearch.value = false), 150);
}
function openResult(r) {
	const map = {
		"Customer Vehicle": () => `/credit/${encodeURIComponent(r.description)}`,
		Customer: () => `/credit/${encodeURIComponent(r.name)}`,
		"Shift Sale Entry": () => `/shifts/${r.name}`,
		"Tanker Receipt": () => `/tankers/${r.name}`,
		"Daily Stock Register": () => `/dsr/${r.name}`,
	};
	q.value = "";
	results.value = [];
	router.push(map[r.doctype]());
}

const watchCollapse = () => localStorage.setItem("pd-collapsed", collapsed.value ? "1" : "0");
let poll;
onMounted(() => {
	poll = setInterval(refreshCounts, 60000);
});
onBeforeUnmount(() => {
	clearInterval(poll);
	watchCollapse();
});
import { watch } from "vue";
watch(collapsed, watchCollapse);
watch(
	() => route.fullPath,
	() => {
		menuOpen.value = false;
		fabOpen.value = false;
	}
);
</script>
