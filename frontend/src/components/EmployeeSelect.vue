<template>
	<select
		:value="modelValue || ''"
		class="inp"
		:disabled="disabled"
		@change="pick($event.target.value)"
	>
		<option value="">{{ placeholder || "Select" }}</option>
		<option v-for="e in list" :key="e.name" :value="e.name">
			{{ e.employee_name }}{{ e.designation ? " · " + e.designation : "" }}
		</option>
	</select>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { getList } from "../api";
import { session } from "../session";
const props = defineProps({ modelValue: String, disabled: Boolean, placeholder: String });
const emit = defineEmits(["update:modelValue", "change"]);
const list = ref([]);
let cache = window.__pdEmployees;
function pick(v) {
	emit("update:modelValue", v);
	emit("change", v);
}
onMounted(async () => {
	if (!cache) {
		cache = window.__pdEmployees = getList("Employee", {
			filters: { status: "Active", company: session.boot.station?.company },
			fields: ["name", "employee_name", "designation"],
			order_by: "employee_name asc",
			limit_page_length: 500,
		});
	}
	list.value = await cache;
	if (props.modelValue && !list.value.some((e) => e.name === props.modelValue)) {
		list.value = [...list.value, { name: props.modelValue, employee_name: props.modelValue }];
	}
});
</script>
