<template>
	<Modal
		:model-value="modelValue"
		title="Receive payment"
		@update:model-value="$emit('update:modelValue', $event)"
	>
		<div class="space-y-3">
			<Field label="Customer" required>
				<select v-if="!fixed" v-model="form.customer" class="inp">
					<option value="" disabled>Select</option>
					<option v-for="c in customers" :key="c">{{ c }}</option>
				</select>
				<div v-else class="auto">{{ fixed }}</div>
			</Field>
			<Field label="Amount" required><NumInput v-model="form.amount" big /></Field>
			<Field label="Mode" required
				><select v-model="form.mode_of_payment" class="inp">
					<option v-for="m in modes" :key="m">{{ m }}</option>
				</select></Field
			>
			<div class="grid grid-cols-2 gap-3">
				<Field label="Reference no"
					><input v-model="form.reference_no" class="inp" placeholder="UTR / cheque no"
				/></Field>
				<Field label="Date"
					><input v-model="form.posting_date" type="date" class="inp"
				/></Field>
			</div>
			<p class="text-[12px] text-ink-3">Allocated to the oldest unpaid invoices first.</p>
		</div>
		<template #footer>
			<button class="btn-secondary" @click="$emit('update:modelValue', false)">Close</button>
			<button
				class="btn-primary"
				:disabled="busy || !form.amount || !(fixed || form.customer)"
				@click="submit"
			>
				Receive {{ form.amount ? inr(form.amount) : "" }}
			</button>
		</template>
	</Modal>
</template>
<script setup>
import { ref, reactive, onMounted } from "vue";
import { toast } from "frappe-ui";
import { api, errorText, getList } from "../api";
import { inr, today } from "../format";
import { session } from "../session";
import Modal from "./Modal.vue";
import Field from "./Field.vue";
import NumInput from "./NumInput.vue";
const props = defineProps({ modelValue: Boolean, customers: Array, fixed: String });
const emit = defineEmits(["update:modelValue", "done"]);
const modes = ref([]);
const busy = ref(false);
const form = reactive({
	customer: "",
	amount: 0,
	mode_of_payment: "UPI",
	reference_no: "",
	posting_date: today(),
});
async function submit() {
	busy.value = true;
	try {
		const r = await api("receive_payment", {
			...form,
			customer: props.fixed || form.customer,
		});
		toast.success(
			`Payment ${r.name} recorded${r.unallocated > 0 ? ` (₹${r.unallocated} advance)` : ""}`
		);
		emit("update:modelValue", false);
		emit("done");
		Object.assign(form, { amount: 0, reference_no: "" });
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
}
onMounted(() => {
	modes.value = ["Cash", ...(session.boot.payment_modes || [])];
});
</script>
