<template>
	<div class="relative w-full" :style="{ height: height + 'px' }">
		<div v-if="loading" class="absolute inset-0 animate-pulse rounded-lg bg-slate-100" />
		<div
			v-else-if="isEmpty"
			class="absolute inset-0 flex flex-col items-center justify-center gap-1 text-[13px] text-ink-3"
		>
			<i class="lucide-chart-no-axes-column size-6" />No data for this period
		</div>
		<div v-show="!loading && !isEmpty" ref="el" class="h-full w-full" />
	</div>
</template>
<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import * as echarts from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import {
	GridComponent,
	TooltipComponent,
	LegendComponent,
	MarkLineComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import { fuelClass, FUEL_COLORS, num, compactInr, inr } from "../../format";

echarts.use([
	BarChart,
	LineChart,
	PieChart,
	GridComponent,
	TooltipComponent,
	LegendComponent,
	MarkLineComponent,
	CanvasRenderer,
]);

const props = defineProps({
	type: { type: String, default: "bar" }, // bar | line | donut
	labels: { type: Array, default: () => [] },
	datasets: { type: Array, default: () => [] },
	height: { type: Number, default: 260 },
	stacked: Boolean,
	horizontal: Boolean,
	unit: { type: String, default: "" }, // 'L' | '₹' | ''
	zeroLine: Boolean,
	loading: Boolean,
});
const el = ref(null);
let chart = null;
let ro = null;
const PALETTE = [
	"#0F766E",
	"#2563EB",
	"#D97706",
	"#7C3AED",
	"#DB2777",
	"#64748B",
	"#0891B2",
	"#65A30D",
];
const colorOf = (name, i) =>
	fuelClass(name) !== "lube" ? FUEL_COLORS[fuelClass(name)] : PALETTE[i % PALETTE.length];
const isEmpty = computed(
	() =>
		!props.labels.length ||
		!props.datasets.some((d) => (d.values || []).some((v) => Number(v)))
);
const axisFmt = (v) =>
	props.unit === "₹"
		? compactInr(v).replace("₹ ", "₹")
		: props.unit === "L"
		? `${num(v, 0)}`
		: num(v, 0);
const valFmt = (v) =>
	props.unit === "₹" ? inr(v) : props.unit === "L" ? `${num(v, 0)} L` : num(v, 2);

function option() {
	const base = {
		textStyle: { fontFamily: "Inter, system-ui, sans-serif", color: "#475569" },
		tooltip: {
			trigger: props.type === "donut" ? "item" : "axis",
			backgroundColor: "#fff",
			borderColor: "#E5E7EB",
			borderWidth: 1,
			textStyle: { color: "#0F172A", fontSize: 12 },
			extraCssText: "box-shadow:0 8px 20px rgba(15,23,42,.08);border-radius:8px;",
			axisPointer: {
				type: props.type === "line" ? "line" : "shadow",
				shadowStyle: { color: "rgba(15,118,110,0.06)" },
			},
			valueFormatter: valFmt,
		},
		legend: {
			show: props.datasets.length > 1 || props.type === "donut",
			bottom: 0,
			icon: "roundRect",
			itemWidth: 10,
			itemHeight: 10,
			textStyle: { fontSize: 12, color: "#475569" },
		},
	};
	if (props.type === "donut") {
		const vals = props.datasets[0]?.values || [];
		const total = vals.reduce((a, v) => a + Math.max(Number(v) || 0, 0), 0);
		return {
			...base,
			legend: { ...base.legend, type: "scroll" },
			title: {
				text: props.unit === "₹" ? compactInr(total) : num(total, 0),
				subtext: "Total",
				left: "center",
				top: "36%",
				textStyle: { fontSize: 18, fontWeight: 600, color: "#0F172A" },
				subtextStyle: { fontSize: 11, color: "#94A3B8" },
			},
			series: [
				{
					type: "pie",
					radius: ["52%", "74%"],
					center: ["50%", "44%"],
					avoidLabelOverlap: true,
					label: { show: false },
					itemStyle: { borderColor: "#fff", borderWidth: 2 },
					data: props.labels.map((l, i) => ({
						name: String(l),
						value: Math.max(Number(vals[i]) || 0, 0),
						itemStyle: { color: PALETTE[i % PALETTE.length] },
					})),
				},
			],
		};
	}
	const cat = {
		type: "category",
		data: props.labels.map(String),
		axisTick: { show: false },
		axisLine: { lineStyle: { color: "#E5E7EB" } },
		axisLabel: { color: "#94A3B8", fontSize: 11, hideOverlap: true },
	};
	const val = {
		type: "value",
		splitLine: { lineStyle: { color: "#F1F5F9" } },
		axisLabel: { color: "#94A3B8", fontSize: 11, formatter: axisFmt },
	};
	return {
		...base,
		grid: {
			left: 8,
			right: 12,
			top: 16,
			bottom: props.datasets.length > 1 ? 36 : 8,
			containLabel: true,
		},
		xAxis: props.horizontal ? val : cat,
		yAxis: props.horizontal ? cat : val,
		series: props.datasets.map((d, i) => ({
			name: d.name || "Value",
			type: props.type === "line" ? "line" : "bar",
			data: (d.values || []).map((v) => Number(v) || 0),
			stack: props.stacked ? "total" : undefined,
			smooth: props.type === "line",
			symbol: "circle",
			symbolSize: 5,
			showSymbol: false,
			barMaxWidth: 28,
			itemStyle: {
				color: colorOf(d.name || "", i),
				borderRadius: props.stacked && i < props.datasets.length - 1 ? 0 : [3, 3, 0, 0],
			},
			lineStyle: { width: 2 },
			markLine:
				i === 0 && props.zeroLine
					? {
							silent: true,
							symbol: "none",
							label: { show: false },
							lineStyle: { color: "#CBD5E1", type: "dashed" },
							data: [{ yAxis: 0 }],
					  }
					: undefined,
		})),
	};
}
function render() {
	if (!el.value || props.loading || isEmpty.value) return;
	if (!chart) chart = echarts.init(el.value, null, { renderer: "canvas" });
	chart.setOption(option(), true);
	chart.resize();
}
onMounted(() => {
	nextTick(render);
	ro = new ResizeObserver(() => chart && chart.resize());
	if (el.value) ro.observe(el.value);
});
watch(
	() => [props.labels, props.datasets, props.loading, props.type, props.stacked],
	() => nextTick(render),
	{ deep: true }
);
onBeforeUnmount(() => {
	ro && ro.disconnect();
	chart && chart.dispose();
	chart = null;
});
</script>
