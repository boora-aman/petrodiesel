<template>
  <div v-if="f.doc.value">
    <PageHeader :title="f.isNew.value ? 'New stock transfer' : d.name" back="/transfers" :subtitle="`${d.from_warehouse || 'From'} → ${d.to_warehouse || 'To'}`">
      <template #badge><StatusPill :status="f.state.value" /></template>
      <template #actions><FormActions :form="f" /></template>
    </PageHeader>
    <div v-if="f.serverError.value && ed && d.items.every((r) => r.item_code && r.qty)" class="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[13px] text-amber-800">{{ f.serverError.value }}</div>
    <div class="card card-pad mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
      <Field label="Type"><select v-model="d.transfer_type" class="inp" :disabled="!ed" @change="d.from_warehouse = ''; d.to_warehouse = ''"><option>Lube / Shop Stock</option><option>Fuel Tank to Tank</option></select></Field>
      <Field label="Date"><input v-model="d.posting_date" type="date" class="inp" :disabled="!ed" /></Field>
      <Field label="From" required><select v-model="d.from_warehouse" class="inp" :disabled="!ed" @change="calc"><option value="" disabled>Select</option><option v-for="w in warehouses" :key="w.value" :value="w.value">{{ w.label }}</option></select></Field>
      <Field label="To" required><select v-model="d.to_warehouse" class="inp" :disabled="!ed"><option value="" disabled>Select</option><option v-for="w in warehouses.filter((x) => x.value !== d.from_warehouse)" :key="w.value" :value="w.value">{{ w.label }}</option></select></Field>
    </div>
    <Section title="Items">
      <template #actions><button v-if="ed" class="btn-secondary btn-sm" @click="d.items.push({ qty: 0, _key: nextKey() })"><i class="lucide-plus size-3.5" />Add item</button></template>
      <div v-for="r in d.items" :key="r._key" class="mb-2 grid grid-cols-12 items-end gap-2">
        <div class="col-span-12 sm:col-span-6"><Field label="Item"><LinkInput v-model="r.item_code" doctype="Item" :filters="d.transfer_type === 'Fuel Tank to Tank' ? { petro_product_type: 'Fuel' } : { is_stock_item: 1 }" :disabled="!ed" @change="calc" /></Field></div>
        <div class="col-span-5 sm:col-span-3"><AutoField label="Available" :value="num(r.available_qty)" /></div>
        <div class="col-span-5 sm:col-span-2"><Field label="Qty" :error="r.qty > r.available_qty ? 'More than available' : ''"><NumInput v-model="r.qty" :disabled="!ed" /></Field></div>
        <button v-if="ed" class="col-span-2 pb-2 text-red-600 sm:col-span-1" title="Remove" @click="d.items.splice(d.items.indexOf(r), 1)"><i class="lucide-trash-2 size-4" /></button>
      </div>
      <Field label="Reason" class="mt-3"><input v-model="d.remarks" class="inp" :disabled="!ed" /></Field>
    </Section>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDocForm, nextKey } from '../composables/useDocForm'
import { api, getList } from '../api'
import { session } from '../session'
import { num, today } from '../format'
import PageHeader from '../components/PageHeader.vue'
import Section from '../components/Section.vue'
import Field from '../components/Field.vue'
import AutoField from '../components/AutoField.vue'
import NumInput from '../components/NumInput.vue'
import LinkInput from '../components/LinkInput.vue'
import StatusPill from '../components/StatusPill.vue'
import FormActions from '../components/FormActions.vue'
const props = defineProps({ name: String })
const tanks = ref([])
const stores = ref([])
const f = useDocForm({ doctype: 'Internal Stock Transfer', name: props.name, route: '/transfers', tables: ['items'],
  blank: () => ({ doctype: 'Internal Stock Transfer', station: session.station, posting_date: today(), transfer_type: 'Lube / Shop Stock',
    from_warehouse: '', to_warehouse: '', items: [{ qty: 0 }] }) })
const d = computed(() => f.doc.value)
const ed = computed(() => f.editable.value)
const warehouses = computed(() => (d.value.transfer_type === 'Fuel Tank to Tank'
  ? tanks.value.map((t) => ({ value: t.warehouse, label: `${t.name} (${t.fuel_item})` }))
  : stores.value.map((w) => ({ value: w.name, label: w.name }))))
async function calc() {
  for (const r of d.value.items) {
    if (r.item_code && d.value.from_warehouse) {
      r.available_qty = await api('petrodiesel.petrodiesel.doctype.internal_stock_transfer.internal_stock_transfer.get_available', { item_code: r.item_code, warehouse: d.value.from_warehouse })
    }
  }
}
onMounted(async () => {
  tanks.value = await getList('Fuel Tank Master', { filters: { station: session.station }, fields: ['name', 'warehouse', 'fuel_item'] })
  const tankWh = tanks.value.map((t) => t.warehouse)
  stores.value = (await getList('Warehouse', { filters: { company: session.boot.station?.company, is_group: 0 }, fields: ['name'], limit_page_length: 200 }))
    .filter((w) => !tankWh.includes(w.name))
  await f.load()
})
</script>
