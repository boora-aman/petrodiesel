<template>
	<div>
		<PageHeader title="Alerts" subtitle="What needs attention at the outlet">
			<template #actions
				><button v-if="logs.some((l) => !l.read)" class="btn-secondary" @click="markRead">
					Mark all read
				</button></template
			>
		</PageHeader>
		<div v-if="loading"><Skeleton class="h-40 w-full" /></div>
		<template v-else>
			<Section title="Live checks" flush class="mb-4">
				<EmptyState
					v-if="!alerts.length"
					title="All caught up"
					icon="lucide-circle-check"
				/>
				<div class="divide-y divide-line">
					<div v-for="(a, i) in alerts" :key="i" class="flex gap-3 px-4 py-3">
						<span
							class="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full"
							:class="a.severity === 'danger' ? 'bg-red-50' : 'bg-amber-50'"
						>
							<i
								:class="[
									icon(a.type),
									a.severity === 'danger' ? 'text-red-600' : 'text-amber-600',
								]"
								class="size-4"
							/>
						</span>
						<div class="min-w-0 flex-1">
							<div class="text-[13px] font-medium">{{ a.title }}</div>
							<div class="text-[12px] text-ink-2">{{ a.detail }}</div>
						</div>
						<span
							class="pill h-fit"
							:class="
								a.severity === 'danger'
									? 'border-red-200 bg-red-50 text-red-700'
									: 'border-amber-200 bg-amber-50 text-amber-700'
							"
							>{{ a.type }}</span
						>
					</div>
				</div>
			</Section>
			<Section title="Notifications" flush>
				<EmptyState v-if="!logs.length" title="No notifications" />
				<div class="divide-y divide-line">
					<div
						v-for="l in logs"
						:key="l.name"
						class="flex gap-3 px-4 py-3"
						:class="!l.read ? 'bg-brand-50/40' : ''"
					>
						<span
							class="mt-1.5 size-2 shrink-0 rounded-full"
							:class="!l.read ? 'bg-brand-600' : 'bg-transparent'"
						/>
						<div class="min-w-0 flex-1">
							<div class="text-[13px]">{{ l.subject }}</div>
							<div class="text-[11px] text-ink-3">
								{{ relTime(l.creation) }} · {{ l.document_type }}
								{{ l.document_name }}
							</div>
						</div>
					</div>
				</div>
			</Section>
		</template>
	</div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { toast } from "frappe-ui";
import { api, errorText } from "../api";
import { refreshCounts } from "../session";
import { relTime } from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import EmptyState from "../components/EmptyState.vue";
import Skeleton from "../components/Skeleton.vue";
const alerts = ref([]);
const logs = ref([]);
const loading = ref(true);
const icon = (t) =>
	({
		shift: "lucide-receipt-indian-rupee",
		tanker: "lucide-truck",
		dsr: "lucide-notebook-tabs",
		nozzle: "lucide-wrench",
		compliance: "lucide-shield-alert",
		stock: "lucide-fuel",
		credit: "lucide-credit-card",
	}[t] || "lucide-info");
async function load() {
	try {
		const r = await api("notifications");
		alerts.value = r.alerts;
		logs.value = r.logs;
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		loading.value = false;
	}
}
async function markRead() {
	await api("mark_notifications_read");
	await load();
	refreshCounts();
}
onMounted(load);
</script>
