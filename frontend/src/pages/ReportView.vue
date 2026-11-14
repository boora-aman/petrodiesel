<template>
  <div class="report-page">
    <PageHeader :title="report" :subtitle="meta?.desc" back="/reports">
      <template #actions>
        <button class="btn-secondary" :disabled="!rows.length" @click="exportCsv"><i class="lucide-download size-4" /><span class="hidden sm:inline">CSV</span></button>
        <button class="btn-secondary" :disabled="!rows.length" @click="print"><i class="lucide-printer size-4" /><span class="hidden sm:inline">Print</span></button>
        <a class="btn-secondary" :href="deskLink" target="_blank" title="Open in ERPNext Desk"><i class="lucide-external-link size-4" /></a>
      </template>
    </PageHeader>

    <div class="card mb-4 p-3 print:hidden">
      <div class="flex flex-wrap items-end gap-2">
        <template v-if="has('dates')">
          <Field label="From"><input v-model="f.from_date" type="date" class="inp w-[150px]" @change="run" /></Field>
          <Field label="To"><input v-model="f.to_date" type="date" class="inp w-[150px]" @change="run" /></Field>
          <div class="flex flex-wrap gap-1">
            <button v-for="p in presets" :key="p.l" class="btn-ghost btn-sm" @click="preset(p.d)">{{ p.l }}</button>
          </div>
        </template>
        <Field v-if="has('date')" label="Business date"><input v-model="f.posting_date" type="date" class="inp w-[160px]" @change="run" /></Field>
        <Field v-if="has('asof')" label="As on"><input v-model="f.to_date" type="date" class="inp w-[160px]" @change="run" /></Field>
        <Field v-if="has('customer')" label="Customer" required><LinkInput v-model="f.customer" doctype="Customer" @change="run" /></Field>
        <Field v-if="has('employee')" label="Employee (ledger)"><EmployeeSelect v-model="f.employee" placeholder="All employees" @change="run" /></Field>
        <Field v-if="has('days')" label="Expiring within (days)"><NumInput v-model="f.days" class="w-28" @update:model-value="debouncedRun" /></Field>
        <div class="relative ml-auto w-full sm:w-56">
          <i class="lucide-search absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-3" />
          <input v-model="q" class="inp pl-9" placeholder="Filter rows…" @input="page = 1" />
        </div>
      </div>
    </div>

    <div class="mb-3 hidden print:block">
      <div class="text-[16px] font-semibold">{{ session.boot.station?.station_name }} — {{ report }}</div>
      <div class="text-[12px]">{{ filterText }}</div>
    </div>

    <div v-if="kpis.length" class="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
      <div v-for="k in kpis" :key="k.label" class="card card-pad">
        <div class="text-[12px] text-ink-2">{{ k.label }}</div>
        <div class="num mt-1 text-[20px] font-semibold" :class="k.neg ? 'text-red-600' : ''">{{ k.value }}</div>
      </div>
    </div>

    <Section v-if="chart && !loading" class="mb-4 print:break-inside-avoid" :title="chartTitle">
      <Chart :type="chart.type === 'donut' || chart.type === 'pie' ? 'donut' : chart.type === 'line' ? 'line' : 'bar'"
        :labels="chart.data.labels" :datasets="chart.data.datasets" :stacked="!!chart.barOptions?.stacked"
        :unit="chart.fieldtype === 'Currency' ? '₹' : chart.fieldtype === 'Float' ? 'L' : ''" :zero-line="chart.type === 'line'" />
    </Section>

    <div class="card overflow-hidden">
      <div v-if="loading" class="space-y-2 p-4"><Skeleton v-for="i in 8" :key="i" class="h-8 w-full" /></div>
      <div v-else-if="error" class="flex items-center gap-2 p-4 text-[13px] text-red-600"><i class="lucide-circle-alert size-4" />{{ error }}</div>
      <EmptyState v-else-if="!filtered.length" title="No data" :text="q ? 'No rows match the filter.' : 'Change the filters and try again.'" />
      <template v-else>
        <div class="max-h-[70vh] overflow-auto print:max-h-none print:overflow-visible">
          <table class="tbl">
            <thead class="sticky top-0 z-[1]">
              <tr>
                <th v-for="c in cols" :key="c.fieldname" class="cursor-pointer select-none hover:text-ink" :class="isNum(c) ? '!text-right' : ''" @click="sortBy(c)">
                  <span class="inline-flex items-center gap-1">{{ c.label }}<i v-if="sort.key === c.fieldname" :class="sort.dir === 1 ? 'lucide-arrow-up' : 'lucide-arrow-down'" class="size-3" /></span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in paged" :key="i" :class="r.bold ? 'bg-slate-50 font-semibold' : ''">
                <td v-for="(c, j) in cols" :key="c.fieldname" :class="[isNum(c) ? 'r' : '', j === 0 && r.indent ? 'pl-8' : '', numClass(r[c.fieldname], c)]">
                  <a v-if="linkOf(r, c)" :href="linkOf(r, c)" class="text-brand-700 hover:underline" @click.prevent="openLink(r, c)">{{ fmt(r[c.fieldname], c) }}</a>
                  <template v-else>{{ fmt(r[c.fieldname], c) }}</template>
                </td>
              </tr>
            </tbody>
            <tfoot v-if="totalRow" class="sticky bottom-0">
              <tr class="bg-slate-100 font-semibold">
                <td v-for="(c, j) in cols" :key="c.fieldname" class="border-t border-line px-3 py-2" :class="isNum(c) ? 'r' : ''">{{ j === 0 ? 'Total' : isNum(c) && c.fieldtype !== 'Percent' ? fmt(totalRow[c.fieldname], c) : '' }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <div class="flex flex-wrap items-center gap-3 border-t border-line px-4 py-2.5 text-[12px] text-ink-2 print:hidden">
          <span>Showing <b class="num">{{ pageStart + 1 }}–{{ pageStart + paged.length }}</b> of <b class="num">{{ filtered.length }}</b> rows</span>
          <label class="flex items-center gap-1.5">Rows
            <select v-model.number="pageSize" class="inp !h-7 w-20 !px-1.5 text-[12px]" @change="page = 1"><option :value="50">50</option><option :value="100">100</option><option :value="100000">All</option></select>
          </label>
          <div class="ml-auto flex gap-1">
            <button class="btn-secondary btn-sm !px-2" :disabled="page === 1" @click="page--"><i class="lucide-chevron-left size-3.5" /></button>
            <span class="px-2 py-1">Page {{ page }} / {{ pages }}</span>
            <button class="btn-secondary btn-sm !px-2" :disabled="page >= pages" @click="page++"><i class="lucide-chevron-right size-3.5" /></button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api, errorText, deskUrl } from '../api'
import { session } from '../session'
import { REPORTS } from '../reports'
import { inr, num, dateFmt, today, addDays, compactInr } from '../format'
import PageHeader from '../components/PageHeader.vue'
import Section from '../components/Section.vue'
import Field from '../components/Field.vue'
import NumInput from '../components/NumInput.vue'
import LinkInput from '../components/LinkInput.vue'
import EmployeeSelect from '../components/EmployeeSelect.vue'
import Skeleton from '../components/Skeleton.vue'
import EmptyState from '../components/EmptyState.vue'
import Chart from '../components/charts/Chart.vue'

const props = defineProps({ report: String })
const router = useRouter()
const meta = computed(() => REPORTS.find((r) => r.name === props.report) || { filters: ['station', 'dates'] })
const has = (k) => meta.value?.filters.includes(k)
const f = reactive({ from_date: addDays(today(), -(meta.value?.days || 30)), to_date: today(), posting_date: addDays(today(), -1),
  customer: '', employee: '', days: 90 })
const cols = ref([])
const rows = ref([])
const totalRow = ref(null)
const chart = ref(null)
const loading = ref(false)
const error = ref('')
const q = ref('')
const page = ref(1)
const pageSize = ref(50)
const sort = reactive({ key: '', dir: -1 })
const presets = [{ l: 'Today', d: 0 }, { l: '7 days', d: 6 }, { l: '30 days', d: 29 }, { l: 'This month', d: 'm' }, { l: '90 days', d: 89 }]
const deskLink = computed(() => `/desk/query-report/${encodeURIComponent(props.report)}`)
const chartTitle = computed(() => ({ bar: 'Overview', line: 'Trend', donut: 'Share', pie: 'Share' })[chart.value?.type] || 'Overview')
const isNum = (c) => ['Currency', 'Float', 'Int', 'Percent'].includes(c.fieldtype)
const numClass = (v, c) => (isNum(c) && Number(v) < 0 && /short|variance|loss|excess|growth|gain/i.test(c.fieldname + c.label) ? 'text-red-600' : '')
const filterText = computed(() => [has('dates') && `${dateFmt(f.from_date)} – ${dateFmt(f.to_date)}`, has('date') && dateFmt(f.posting_date),
  f.customer, q.value && `filter "${q.value}"`].filter(Boolean).join(' · '))

function fmt(v, c) {
  if (v === null || v === undefined || v === '') return ''
  if (c.fieldtype === 'Currency') return inr(v)
  if (c.fieldtype === 'Float') return num(v)
  if (c.fieldtype === 'Int') return num(v, 0)
  if (c.fieldtype === 'Percent') return num(v, 2) + '%'
  if (c.fieldtype === 'Date') return dateFmt(v)
  if (c.fieldtype === 'Check') return v ? '✓' : '✗'
  if (c.fieldtype === 'Datetime') return dateFmt(v) + ' ' + String(v).slice(11, 16)
  return v
}
const APP_ROUTES = { 'Shift Sale Entry': '/shifts/', 'Tanker Receipt': '/tankers/', 'Daily Stock Register': '/dsr/', 'Tank Dip Reading': '/dips/',
  'Credit Bill': '/credit-bills/', 'Shop Purchase': '/purchases/', 'Internal Stock Transfer': '/transfers/', Customer: '/credit/' }
function linkDoctype(r, c) {
  if (c.fieldtype === 'Link') return c.options
  if (c.fieldtype === 'Dynamic Link') return r[c.options]
  return null
}
function linkOf(r, c) {
  const dt = linkDoctype(r, c)
  if (!dt || !r[c.fieldname]) return null
  return APP_ROUTES[dt] ? `/petrodiesel${APP_ROUTES[dt]}${encodeURIComponent(r[c.fieldname])}` : deskUrl(dt, r[c.fieldname])
}
function openLink(r, c) {
  const dt = linkDoctype(r, c)
  if (APP_ROUTES[dt]) router.push(APP_ROUTES[dt] + encodeURIComponent(r[c.fieldname]))
  else window.open(deskUrl(dt, r[c.fieldname]), '_blank')
}
const filtered = computed(() => {
  let out = rows.value
  if (q.value) {
    const s = q.value.toLowerCase()
    out = out.filter((r) => cols.value.some((c) => String(fmt(r[c.fieldname], c)).toLowerCase().includes(s)))
  }
  if (sort.key) {
    const c = cols.value.find((x) => x.fieldname === sort.key)
    out = [...out].sort((a, b) => {
      const x = a[sort.key], y = b[sort.key]
      if (isNum(c)) return ((Number(x) || 0) - (Number(y) || 0)) * sort.dir
      return String(x ?? '').localeCompare(String(y ?? '')) * sort.dir
    })
  }
  return out
})
const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
const pageStart = computed(() => (page.value - 1) * pageSize.value)
const paged = computed(() => filtered.value.slice(pageStart.value, pageStart.value + pageSize.value))
const kpis = computed(() => {
  if (!totalRow.value) return []
  return cols.value.filter((c) => ['Currency', 'Float'].includes(c.fieldtype) && totalRow.value[c.fieldname]).slice(0, 4)
    .map((c) => ({ label: c.label, value: c.fieldtype === 'Currency' ? compactInr(totalRow.value[c.fieldname]) : num(totalRow.value[c.fieldname], 0), neg: Number(totalRow.value[c.fieldname]) < 0 }))
})
function sortBy(c) {
  if (sort.key === c.fieldname) sort.dir = -sort.dir
  else { sort.key = c.fieldname; sort.dir = isNum(c) ? -1 : 1 }
}
function preset(d) {
  f.to_date = today()
  f.from_date = d === 'm' ? today().slice(0, 8) + '01' : addDays(today(), -d)
  run()
}
let t
function debouncedRun() { clearTimeout(t); t = setTimeout(run, 400) }
async function run() {
  if (has('customer') && !f.customer) { error.value = 'Choose a customer to see the statement.'; rows.value = []; return }
  loading.value = true; error.value = ''; page.value = 1
  try {
    const filters = { station: session.station }
    if (has('dates')) Object.assign(filters, { from_date: f.from_date, to_date: f.to_date })
    if (has('date')) filters.posting_date = f.posting_date
    if (has('asof')) filters.to_date = f.to_date
    if (has('customer')) Object.assign(filters, { customer: f.customer, company: session.boot.station?.company })
    if (has('employee') && f.employee) filters.employee = f.employee
    if (has('days')) filters.days = f.days
    const r = await api('frappe.desk.query_report.run', { report_name: props.report, filters })
    const columns = (r.columns || []).map((c) => (typeof c === 'string' ? { label: c, fieldname: c } : c))
    cols.value = columns.filter((c) => !c.hidden)
    const res = (r.result || []).filter((x) => x && !Array.isArray(x))
    const last = r.result?.[r.result.length - 1]
    totalRow.value = null
    if (Array.isArray(last)) {
      const tr = {}
      last.forEach((v, i) => { if (columns[i]) tr[columns[i].fieldname] = v })
      totalRow.value = tr
    }
    rows.value = res
    chart.value = r.chart && r.chart.data && r.chart.data.labels?.length ? r.chart : null
  } catch (e) { error.value = errorText(e) } finally { loading.value = false }
}
function exportCsv() {
  const head = cols.value.map((c) => `"${c.label}"`).join(',')
  const body = filtered.value.map((r) => cols.value.map((c) => `"${String(r[c.fieldname] ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob(['﻿' + head + '\n' + body], { type: 'text/csv;charset=utf-8' }))
  a.download = `${props.report} ${today()}.csv`
  a.click()
}
function print() { pageSize.value = 100000; setTimeout(() => window.print(), 100) }
onMounted(() => { if (!has('customer')) run() })
</script>
