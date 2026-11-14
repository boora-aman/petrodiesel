<template>
	<div class="flex flex-wrap items-center gap-2">
		<a v-if="printUrl" :href="printUrl" target="_blank" class="btn-secondary"
			><i class="lucide-printer size-4" /><span class="hidden sm:inline">Print</span></a
		>
		<button
			v-if="f.editable.value"
			class="btn-secondary"
			:disabled="f.busy.value"
			@click="f.save()"
		>
			<i class="lucide-save size-4" />Save draft
		</button>
		<button
			v-if="f.sendAction.value"
			class="btn-primary"
			:disabled="f.busy.value || blocked"
			:title="blocked ? blockedReason : ''"
			@click="f.save(f.sendAction.value)"
		>
			<i class="lucide-send size-4" />{{ sendLabel }}
		</button>
		<button
			v-for="t in others"
			:key="t"
			:class="/Reject|Cancel/.test(t) ? 'btn-secondary !text-red-600' : 'btn-primary'"
			:disabled="f.busy.value"
			@click="run(t)"
		>
			{{ t }}
		</button>
		<button
			v-if="canPlainCancel"
			class="btn-secondary !text-red-600"
			:disabled="f.busy.value"
			@click="f.act('cancel_doc')"
		>
			Cancel
		</button>
	</div>
	<Modal v-model="rejecting" title="Reject">
		<Field label="Reason" required><textarea v-model="reason" class="inp h-24 py-2" /></Field>
		<template #footer>
			<button class="btn-secondary" @click="rejecting = false">Close</button>
			<button
				class="btn-danger"
				:disabled="!reason"
				@click="
					rejecting = false;
					f.act('Reject', reason);
				"
			>
				Reject
			</button>
		</template>
	</Modal>
</template>
<script setup>
import { computed, ref } from "vue";
import Modal from "./Modal.vue";
import Field from "./Field.vue";
const props = defineProps({
	form: Object,
	printUrl: String,
	blocked: Boolean,
	blockedReason: String,
});
const f = props.form;
const rejecting = ref(false);
const reason = ref("");
const sendLabel = computed(() => {
	const a = f.sendAction.value;
	if (a === "auto" || a === "submit") return "Submit";
	return a;
});
const others = computed(() => f.transitions.value.filter((t) => !/Submit for|Send for/.test(t)));
const canPlainCancel = computed(
	() =>
		!f.isNew.value &&
		f.doc.value?.docstatus === 1 &&
		!f.transitions.value.length &&
		f.full.value?.can_cancel
);
function run(t) {
	if (t === "Reject") {
		rejecting.value = true;
		return;
	}
	f.act(t);
}
</script>
