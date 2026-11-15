<template>
	<input
		:value="display"
		type="text"
		inputmode="decimal"
		class="inp num text-right"
		:class="[big ? 'inp-lg' : '', invalid ? '!border-red-400 !ring-red-100' : '']"
		:disabled="disabled"
		:placeholder="placeholder"
		@input="onInput"
		@focus="$event.target.select()"
	/>
</template>
<script setup>
import { computed } from "vue";
import { num } from "../format";
const props = defineProps({
	modelValue: [Number, String],
	big: Boolean,
	disabled: Boolean,
	invalid: Boolean,
	placeholder: String,
});
const emit = defineEmits(["update:modelValue"]);
const display = computed(() =>
	props.modelValue === null || props.modelValue === undefined || props.modelValue === ""
		? ""
		: props.disabled
		? num(props.modelValue)
		: props.modelValue
);
function onInput(e) {
	const raw = e.target.value.replace(/[^0-9.\-]/g, "");
	if (raw !== e.target.value) e.target.value = raw;
	emit("update:modelValue", raw === "" || raw === "-" || raw === "." ? 0 : Number(raw));
}
</script>
