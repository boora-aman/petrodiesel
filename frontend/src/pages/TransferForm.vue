<template>
  <div v-if="f.doc.value">
    <PageHeader :title="f.isNew.value ? 'New stock transfer' : d.name" back="/transfers" :subtitle="`${label(d.from_warehouse) || 'From'} → ${label(d.to_warehouse) || 'To'}`">
      <template #badge><StatusPill :status="f.state.value" /></template>
      <template #actions><FormActions :form="f" :blocked="!!problem" :blocked-reason="problem" /></template>
    </PageHeader>

    <div class="card card-pad mb-4">
      <div class="mb-3 flex flex-wrap gap-2">
        <button v-for="t in types" :key="t.value" class="flex-1 rounded-lg border px-3 py-2.5 text-left" :disabled="!ed"
          :class="d.transfer_type === t.value ? 'border-brand-600 bg-brand-50' : 'border-line'" @click="setType(t.value)">
          <div class="text-[13px] font-semibold">{{ t.title }}</div>
          <div class="text-[12px] text-ink-2">{{ t.desc }}</div>
        </button>
      </div>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Field label="Date"><input v-model="d.posting_date" type="date" class="inp" :disabled="!ed" /></Field>
        <template v-if="isTank">
          <Field label="From tank" required>
            <select v-model="d.from_warehouse" class="inp" :disabled="!ed" @change="onFromTank">
              <option value="" disabled>Select tank</option>
              <option v-for="t in tanks" :key="t.warehouse" :value="t.warehouse">{{ t.name }} — {{ t.fuel_item }}</option>
            </select>
          </Field>
          <Field label="To tank" required :hint="fromTank ? `Only ${fromTank.fuel_item} tanks are shown` : 'Choose the source tank first'">
            <select v-model="d.to_warehouse" class="inp" :disabled="!ed || !fromTank">
              <option value="" disabled>{{ sameFuelTargets.length ? 'Select tank' : 'No other ' + (fromTank?.fuel_item || '') + ' tank' }}</option>
              <option v-for="t in sameFuelTargets" :key="t.warehouse" :value="t.warehouse">{{ t.name }} — {{ t.fuel_item }}</option>
            </select>
          </Field>
        </template>
        <template v-else>
          <Field label="From store" required>
            <select v-model="d.from_warehouse" class="inp" :disabled="!ed" @change="calc"><option value="" disabled>Select</option><option v-for="w in stores" :key="w.name" :value="w.name">{{ w.name }}</option></select>
          </Field>
          <Field label="To store" required :hint="stores.length < 2 ? 'Only one store exists. Add another warehouse in ERPNext to move shop stock.' : ''">
            <select v-model="d.to_warehouse" class="inp" :disabled="!ed"><option value="" disabled>Select</option><option v-for="w in stores.filter((x) => x.name !== d.from_warehouse)" :key="w.name" :value="w.name">{{ w.name }}</option></select>
          </Field>
        </template>
      </div>
    </div>

    <Section :title="isTank ? 'Fuel to move' : 'Items'">
      <template v-if="!isTank && ed" #actions><button class="btn-secondary btn-sm" @click="d.items.push({ qty: 0, _key: nextKey() })"><i class="lucide-plus size-3.5" />Add item</button></template>
      <div v-if="isTank" class="grid grid-cols-1 items-end gap-3 sm:grid-cols-3">
        <div><div class="lbl mb-1">Fuel</div><div class="flex h-9 items-center"><FuelChip v-if="fromTank" :item="fromTank.fuel_item" /><span v-else class="text-[13px] text-ink-3">Comes from the source tank</span></div></div>
        <AutoField label="Available in source tank (L)" :value="num(d.items[0]?.available_qty)" />
        <Field label="Litres to move" required :error="d.items[0] && d.items[0].qty > d.items[0].available_qty ? 'More than available' : ''"><NumInput v-model="d.items[0].qty" big :disabled="!ed || !fromTank" /></Field>
      </div>
      <template v-else>
        <div v-for="r in d.items" :key="r._key" class="mb-2 grid grid-cols-12 items-end gap-2">
          <div class="col-span-12 sm:col-span-6"><Field label="Item"><LinkInput v-model="r.item_code" doctype="Item" :filters="{ petro_product_type: ['in', ['Lubricant', 'Accessory', 'Other']] }" :disabled="!ed" @change="calc" /></Field></div>
          <div class="col-span-5 sm:col-span-3"><AutoField label="Available" :value="num(r.available_qty)" /></div>
          <div class="col-span-5 sm:col-span-2"><Field label="Qty" :error="r.qty > r.available_qty ? 'More than available' : ''"><NumInput v-model="r.qty" :disabled="!ed" /></Field></div>
          <button v-if="ed && d.items.length > 1" class="col-span-2 pb-2 text-red-600 sm:col-span-1" title="Remove" @click="d.items.splice(d.items.indexOf(r), 1)"><i class="lucide-trash-2 size-4" /></button>
        </div>
      </template>
      <Field label="Reason" class="mt-3"><input v-model="d.remarks" class="inp" :disabled="!ed" placeholder="e.g. tank cleaning, shifting stock to godown" /></Field>
      <div v-if="problem && ed" class="mt-3 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] text-amber-800"><i class="lucide-triangle-alert mt-0.5 size-4" />{{ problem }}</div>
    </Section>
    <a v-if="d.stock_entry" :href="deskUrl('Stock Entry', d.stock_entry)" target="_blank" class="mt-3 inline-flex text-[13px] text-brand-600 hover:underline">Stock Entry {{ d.stock_entry }} →</a>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDocForm, nextKey } from '../composables/useDocForm'
import { api, getList, deskUrl } from '../api'
import { session } from '../session'
import { num, today, flt } from '../format'
import PageHeader from '../components/PageHeader.vue'
import Section from '../components/Section.vue'
import Field from '../components/Field.vue'
import AutoField from '../components/AutoField.vue'
import NumInput from '../components/NumInput.vue'
import LinkInput from '../components/LinkInput.vue'
import FuelChip from '../components/FuelChip.vue'
import StatusPill from '../components/StatusPill.vue'
import FormActions from '../components/FormActions.vue'

const props = defineProps({ name: String })
const types = [
  { value: 'Lube / Shop Stock', title: 'Shop stock', desc: 'Lubricants and accessories between stores' },
  { value: 'Fuel Tank to Tank', title: 'Tank to tank', desc: 'Same fuel only, e.g. during tank cleaning' },
]
const tanks = ref([])
const stores = ref([])
const f = useDocForm({ doctype: 'Internal Stock Transfer', name: props.name, route: '/transfers', tables: ['items'],
  blank: () => ({ doctype: 'Internal Stock Transfer', station: session.station, posting_date: today(), transfer_type: 'Lube / Shop Stock',
    from_warehouse: '', to_warehouse: '', items: [{ qty: 0 }] }) })
const d = computed(() => f.doc.value)
const ed = computed(() => f.editable.value)
const isTank = computed(() => d.value.transfer_type === 'Fuel Tank to Tank')
const fromTank = computed(() => tanks.value.find((t) => t.warehouse === d.value.from_warehouse))
const sameFuelTargets = computed(() => tanks.value.filter((t) => fromTank.value && t.fuel_item === fromTank.value.fuel_item && t.warehouse !== d.value.from_warehouse))
const label = (w) => tanks.value.find((t) => t.warehouse === w)?.name || w
const problem = computed(() => {
  const x = d.value
  if (!x.from_warehouse || !x.to_warehouse) return 'Choose where the stock moves from and to.'
  if (isTank.value && !sameFuelTargets.value.some((t) => t.warehouse === x.to_warehouse)) return 'The target tank must hold the same fuel.'
  if (x.items.some((r) => !r.item_code || !flt(r.qty))) return 'Enter the quantity to move.'
  if (x.items.some((r) => flt(r.qty) > flt(r.available_qty))) return 'Quantity is more than available.'
  return ''
})
function setType(t) {
  d.value.transfer_type = t
  d.value.from_warehouse = ''
  d.value.to_warehouse = ''
  d.value.items = [{ qty: 0, _key: nextKey() }]
}
async function onFromTank() {
  d.value.to_warehouse = ''
  const fuel = fromTank.value?.fuel_item
  d.value.items = [{ item_code: fuel, qty: 0, available_qty: 0, _key: nextKey() }]
  if (sameFuelTargets.value.length === 1) d.value.to_warehouse = sameFuelTargets.value[0].warehouse
  await calc()
}
async function calc() {
  for (const r of d.value.items) {
    if (r.item_code && d.value.from_warehouse) {
      r.available_qty = await api('petrodiesel.petrodiesel.doctype.internal_stock_transfer.internal_stock_transfer.get_available', { item_code: r.item_code, warehouse: d.value.from_warehouse })
    }
  }
}
onMounted(async () => {
  tanks.value = await getList('Fuel Tank Master', { filters: { station: session.station, status: ['!=', 'Inactive'] }, fields: ['name', 'warehouse', 'fuel_item'], order_by: 'name' })
  const tankWh = tanks.value.map((t) => t.warehouse)
  stores.value = (await getList('Warehouse', { filters: { company: session.boot.station?.company, is_group: 0 }, fields: ['name'], limit_page_length: 200 }))
    .filter((w) => !tankWh.includes(w.name) && !/Transit|Work In Progress|Finished Goods/.test(w.name))
  await f.load()
  if (!f.isNew.value) calc()
})
</script>
