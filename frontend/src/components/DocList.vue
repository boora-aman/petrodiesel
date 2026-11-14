<template>
  <div>
    <PageHeader :title="title" :subtitle="subtitle">
      <template #actions>
        <slot name="actions" />
        <RouterLink v-if="newRoute && canCreate" :to="newRoute" class="btn-primary"><i class="lucide-plus size-4" />{{ newLabel }}</RouterLink>
      </template>
    </PageHeader>

    <!-- Toolbar -->
    <div class="card mb-3 p-3">
      <div class="flex flex-wrap items-end gap-2">
        <div class="relative w-full sm:w-64">
          <i class="lucide-search absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-3" />
          <input v-model="search" class="inp pl-9" :placeholder="searchPlaceholder" @input="debouncedReload" />
        </div>
        <template v-if="dateField">
          <Field label="From"><input v-model="from" type="date" class="inp w-[150px]" @change="reload(true)" /></Field>
          <Field label="To"><input v-model="to" type="date" class="inp w-[150px]" @change="reload(true)" /></Field>
          <div class="flex flex-wrap gap-1">
            <button v-for="p in presets" :key="p.label" class="btn-ghost btn-sm" :class="activePreset === p.label ? '!bg-brand-50 !text-brand-700' : ''" @click="applyPreset(p)">{{ p.label }}</button>
          </div>
        </template>
        <Field v-if="statuses" label="Status">
          <select v-model="status" class="inp w-44" @change="reload(true)">
            <option value="">All</option><option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
          </select>
        </Field>
        <slot name="filters" :reload="reload" />
        <div class="ml-auto flex items-center gap-2">
          <span class="text-[12px] text-ink-3">{{ total }} {{ total === 1 ? 'record' : 'records' }}</span>
          <button class="btn-secondary !px-2.5" title="Refresh" @click="reload()"><i class="lucide-refresh-cw size-4" :class="loading ? 'animate-spin' : ''" /></button>
        </div>
      </div>
    </div>

    <div v-if="summary && rows.length" class="mb-3 grid grid-cols-2 gap-2 md:grid-cols-4">
      <div v-for="s in summary(rows)" :key="s.label" class="card px-3 py-2">
        <div class="text-[11px] text-ink-3">{{ s.label }} <span class="text-ink-3/70">· this page</span></div>
        <div class="num text-[15px] font-semibold" :class="s.cls">{{ s.value }}</div>
      </div>
    </div>

    <div class="card overflow-hidden">
      <div v-if="loading && !rows.length" class="space-y-2 p-4"><Skeleton v-for="i in 8" :key="i" class="h-9 w-full" /></div>
      <EmptyState v-else-if="!rows.length" :title="emptyTitle" :text="search || status ? 'No records match these filters.' : 'Nothing recorded in this period yet.'">
        <button v-if="search || status" class="btn-secondary btn-sm" @click="clearFilters">Clear filters</button>
        <RouterLink v-else-if="newRoute && canCreate" :to="newRoute" class="btn-primary btn-sm"><i class="lucide-plus size-3.5" />{{ newLabel }}</RouterLink>
      </EmptyState>
      <template v-else>
        <div class="relative hidden max-h-[65vh] overflow-auto md:block" :class="loading ? 'opacity-60' : ''">
          <table class="tbl">
            <thead class="sticky top-0 z-[1]">
              <tr>
                <th v-for="c in columns" :key="c.key" :class="[c.num ? '!text-right' : '', c.sort !== false ? 'cursor-pointer select-none hover:text-ink' : '']"
                  @click="c.sort !== false && toggleSort(c)">
                  <span class="inline-flex items-center gap-1">{{ c.label }}
                    <i v-if="sortKey === (c.sortKey || c.key)" :class="sortDir === 'asc' ? 'lucide-arrow-up' : 'lucide-arrow-down'" class="size-3" />
                  </span>
                </th>
                <th class="w-8" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rows" :key="r.name" class="group cursor-pointer" @click="open(r)">
                <td v-for="c in columns" :key="c.key" :class="[c.num ? 'r' : '', c.key === 'name' ? 'font-medium text-brand-700' : '']">
                  <slot :name="'cell-' + c.key" :row="r">{{ c.format ? c.format(r[c.key], r) : r[c.key] }}</slot>
                </td>
                <td class="text-ink-3"><i class="lucide-chevron-right size-4 opacity-0 group-hover:opacity-100" /></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="divide-y divide-line md:hidden">
          <button v-for="r in rows" :key="r.name" class="block w-full px-4 py-3 text-left active:bg-gray-50" @click="open(r)">
            <slot name="mobile" :row="r" />
          </button>
        </div>
        <!-- Pagination -->
        <div class="flex flex-wrap items-center gap-3 border-t border-line px-4 py-2.5 text-[12px] text-ink-2">
          <span>Showing <b class="num">{{ start + 1 }}–{{ start + rows.length }}</b> of <b class="num">{{ total }}</b></span>
          <label class="flex items-center gap-1.5">Rows
            <select v-model.number="pageSize" class="inp !h-7 w-16 !px-1.5 text-[12px]" @change="reload(true)"><option v-for="n in [20, 50, 100]" :key="n">{{ n }}</option></select>
          </label>
          <div class="ml-auto flex items-center gap-1">
            <button class="btn-secondary btn-sm !px-2" :disabled="page === 1" title="First page" @click="go(1)"><i class="lucide-chevrons-left size-3.5" /></button>
            <button class="btn-secondary btn-sm !px-2" :disabled="page === 1" title="Previous page" @click="go(page - 1)"><i class="lucide-chevron-left size-3.5" /></button>
            <button v-for="p in pageNumbers" :key="p" class="btn-sm min-w-7 rounded-md px-2 font-medium" :class="p === page ? 'bg-brand-600 text-white' : 'hover:bg-gray-100'" @click="go(p)">{{ p }}</button>
            <button class="btn-secondary btn-sm !px-2" :disabled="page >= pages" title="Next page" @click="go(page + 1)"><i class="lucide-chevron-right size-3.5" /></button>
            <button class="btn-secondary btn-sm !px-2" :disabled="page >= pages" title="Last page" @click="go(pages)"><i class="lucide-chevrons-right size-3.5" /></button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'frappe-ui'
import { api, errorText } from '../api'
import { today, addDays } from '../format'
import { can } from '../session'
import PageHeader from './PageHeader.vue'
import Field from './Field.vue'
import Skeleton from './Skeleton.vue'
import EmptyState from './EmptyState.vue'

const props = defineProps({
  title: String, subtitle: String, doctype: String, fields: Array, columns: Array, newRoute: String,
  newLabel: { type: String, default: 'New' }, routeBase: String, statuses: Array, dateField: { type: [String, Boolean], default: 'posting_date' },
  statusField: { type: String, default: 'workflow_state' }, extraFilters: Object, summary: Function, days: { type: Number, default: 30 },
  emptyTitle: { type: String, default: 'Nothing here yet' }, searchFields: { type: Array, default: () => ['name'] },
  searchPlaceholder: { type: String, default: 'Search by number…' },
})
const router = useRouter()
const key = `pd-list-${props.doctype}`
const saved = (() => { try { return JSON.parse(sessionStorage.getItem(key) || '{}') } catch (e) { return {} } })()
const rows = ref([])
const total = ref(0)
const loading = ref(true)
const from = ref(saved.from || addDays(today(), -props.days))
const to = ref(saved.to || addDays(today(), props.dateField === 'effective_date' ? 60 : 0))
const status = ref(saved.status || '')
const search = ref(saved.search || '')
const page = ref(saved.page || 1)
const pageSize = ref(saved.pageSize || 20)
const sortKey = ref(saved.sortKey || '')
const sortDir = ref(saved.sortDir || 'desc')
const activePreset = ref(saved.preset || '')
const canCreate = can(props.doctype, 'create')
const presets = [
  { label: 'Today', from: () => today(), to: () => today() },
  { label: '7 days', from: () => addDays(today(), -6), to: () => today() },
  { label: '30 days', from: () => addDays(today(), -29), to: () => today() },
  { label: 'This month', from: () => today().slice(0, 8) + '01', to: () => today() },
]
const start = computed(() => (page.value - 1) * pageSize.value)
const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const pageNumbers = computed(() => {
  const n = pages.value, p = page.value
  const s = Math.max(1, Math.min(p - 2, n - 4))
  return Array.from({ length: Math.min(5, n) }, (_, i) => s + i)
})

function filters() {
  const f = []
  if (props.dateField) f.push([props.dateField, 'between', [from.value, to.value]])
  if (status.value) {
    if (status.value === 'Cancelled') f.push(['docstatus', '=', 2])
    else f.push([props.statusField, '=', status.value])
  }
  Object.entries(props.extraFilters || {}).forEach(([k, v]) => v && f.push([k, '=', v]))
  return f
}
function persist() {
  sessionStorage.setItem(key, JSON.stringify({ from: from.value, to: to.value, status: status.value, search: search.value,
    page: page.value, pageSize: pageSize.value, sortKey: sortKey.value, sortDir: sortDir.value, preset: activePreset.value }))
}
async function reload(resetPage = false) {
  if (resetPage === true) page.value = 1
  loading.value = true
  persist()
  try {
    const r = await api('list_docs', { doctype: props.doctype, filters: filters(), fields: props.fields, limit: pageSize.value,
      start: start.value, order_by: sortKey.value ? `${sortKey.value} ${sortDir.value}` : null,
      search: search.value || null, search_fields: props.searchFields })
    rows.value = r.rows
    total.value = r.total
    if (page.value > pages.value) { page.value = pages.value; if (total.value) return reload() }
  } catch (e) { toast.error(errorText(e)) } finally { loading.value = false }
}
let t
function debouncedReload() { clearTimeout(t); t = setTimeout(() => reload(true), 300) }
function go(p) { page.value = Math.min(Math.max(1, p), pages.value); reload() }
function toggleSort(c) {
  const k = c.sortKey || c.key
  if (sortKey.value === k) sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  else { sortKey.value = k; sortDir.value = c.num ? 'desc' : 'asc' }
  reload(true)
}
function applyPreset(p) { from.value = p.from(); to.value = p.to(); activePreset.value = p.label; reload(true) }
function clearFilters() { search.value = ''; status.value = ''; reload(true) }
const open = (r) => router.push(`${props.routeBase}/${encodeURIComponent(r.name)}`)
defineExpose({ reload })
onMounted(() => reload())
</script>
