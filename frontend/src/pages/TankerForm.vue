<template>
  <div v-if="f.doc.value">
    <PageHeader :title="f.isNew.value ? 'New tanker receipt' : d.name" back="/tankers" :subtitle="`${d.truck_no || 'Tank lorry'} · ${dateFmt(d.posting_date)}`">
      <template #badge><StatusPill :status="f.state.value" /></template>
      <template #actions><FormActions :form="f" :blocked="blocked" :blocked-reason="blockReason" /></template>
    </PageHeader>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <div class="space-y-4 lg:col-span-2">
        <Section title="Invoice & vehicle" :step="1">
          <div class="grid grid-cols-2 gap-3 md:grid-cols-3">
            <Field label="Date" required><input v-model="d.posting_date" type="date" class="inp" :disabled="!ed" /></Field>
            <Field label="Time"><input v-model="d.posting_time" type="time" step="1" class="inp" :disabled="!ed" /></Field>
            <Field label="Supplier (OMC)" required><LinkInput v-model="d.supplier" doctype="Supplier" :disabled="!ed" /></Field>
            <Field label="OMC invoice no" required><input v-model="d.supplier_invoice_no" class="inp" :disabled="!ed" /></Field>
            <Field label="Invoice date"><input v-model="d.supplier_invoice_date" type="date" class="inp" :disabled="!ed" /></Field>
            <Field label="Tank lorry no" required><input v-model="d.truck_no" class="inp uppercase" :disabled="!ed" /></Field>
            <Field label="Driver"><input v-model="d.driver_name" class="inp" :disabled="!ed" /></Field>
            <Field label="Received by"><EmployeeSelect v-model="d.received_by" :disabled="!ed" /></Field>
          </div>
        </Section>

        <Section title="Safety checklist" :step="2">
          <div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <Toggle v-model="d.seals_intact" label="Seals intact" :disabled="!ed" />
            <Toggle v-model="d.sales_stopped" label="Sales stopped from tank" :disabled="!ed" />
            <Toggle v-model="d.water_checked" label="Water paste test done" :disabled="!ed" />
          </div>
          <Field class="mt-3" label="Seal numbers"><input v-model="d.seal_numbers" class="inp" :disabled="!ed" /></Field>
          <div v-if="!d.seals_intact" class="mt-2 text-[12px] text-red-600">Seals not intact: describe the problem in remarks.</div>
        </Section>

        <Section title="Products & decantation" :step="3">
          <template #actions><button v-if="ed" class="btn-secondary btn-sm" @click="addItem"><i class="lucide-plus size-3.5" />Add compartment</button></template>
          <div class="space-y-3">
            <div v-for="r in d.items" :key="r._key" class="rounded-lg border p-3" :class="r.challan_density && r.density_at_15 && !densityOk(r) ? 'border-red-300 bg-red-50/40' : 'border-line'">
              <div class="mb-3 flex items-center gap-2">
                <FuelChip v-if="r.fuel_item" :item="r.fuel_item" />
                <span class="text-[13px] font-semibold">{{ r.tank || 'Choose tank' }}</span>
                <button v-if="ed && d.items.length > 1" class="ml-auto text-[12px] text-red-600" @click="d.items.splice(d.items.indexOf(r), 1); calc()">Remove</button>
              </div>
              <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
                <Field label="Tank" required>
                  <select v-model="r.tank" class="inp" :disabled="!ed" @change="onTank(r)"><option v-for="t in tanks" :key="t.name" :value="t.name">{{ t.name }} ({{ t.fuel_item }})</option></select>
                </Field>
                <Field label="Compartment"><input v-model="r.compartment" class="inp" :disabled="!ed" /></Field>
                <Field label="Invoice qty (L)" required><NumInput v-model="r.invoice_qty" :disabled="!ed" @update:model-value="calc" /></Field>
                <Field label="Rate / L" required><NumInput v-model="r.rate" :disabled="!ed" @update:model-value="calc" /></Field>
              </div>
              <div class="mt-3 text-[11px] font-semibold uppercase tracking-wider text-ink-3">Density check (kg/m³)</div>
              <div class="mt-1 grid grid-cols-2 gap-3 md:grid-cols-5">
                <Field label="Challan @15°C"><NumInput v-model="r.challan_density" :disabled="!ed" @update:model-value="calc" /></Field>
                <Field label="Observed"><NumInput v-model="r.observed_density" :disabled="!ed" /></Field>
                <Field label="Temp °C"><NumInput v-model="r.observed_temperature" :disabled="!ed" /></Field>
                <Field label="Density @15°C" hint="From ASTM 53B chart"><NumInput v-model="r.density_at_15" :disabled="!ed" @update:model-value="calc" /></Field>
                <div>
                  <div class="lbl mb-1">Variance</div>
                  <div v-if="r.challan_density && r.density_at_15" class="flex h-9 items-center rounded-lg px-3 text-[13px] font-semibold" :class="densityOk(r) ? 'bg-green-50 text-green-700' : 'bg-red-100 text-red-700'">
                    {{ (r.density_at_15 - r.challan_density > 0 ? '+' : '') + num(r.density_at_15 - r.challan_density, 1) }} · {{ densityOk(r) ? 'OK' : 'Do not decant' }}
                  </div>
                  <div v-else class="auto text-ink-3">—</div>
                </div>
              </div>
              <div class="mt-3 text-[11px] font-semibold uppercase tracking-wider text-ink-3">Dips</div>
              <div class="mt-1 grid grid-cols-2 gap-3 md:grid-cols-4">
                <Field label="Dip before (mm)"><NumInput v-model="r.dip_before_mm" :disabled="!ed" @update:model-value="calc" /></Field>
                <AutoField label="Stock before (L)" :value="num(r.stock_before)" />
                <Field label="Sold during decant (L)"><NumInput v-model="r.sales_during_decantation" :disabled="!ed" @update:model-value="calc" /></Field>
                <Field label="Dip after (mm)"><NumInput v-model="r.dip_after_mm" :disabled="!ed" @update:model-value="calc" /></Field>
                <AutoField label="Stock after (L)" :value="num(r.stock_after)" />
                <AutoField label="Received (L)" :value="num(r.received_qty)" />
                <AutoField label="Short (+) / excess (−)" :value="num(r.shortage_qty)" :tone="r.shortage_qty > 0.5 ? 'bad' : 'good'" />
                <AutoField label="Amount" :value="inr(r.amount)" />
              </div>
            </div>
          </div>
          <label v-if="hasDensityFail && ed" class="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-[13px]">
            <input v-model="d.override_density_check" type="checkbox" :true-value="1" :false-value="0" class="mt-0.5" />
            <span><b>Accept despite density variance</b> (manager only). Record the reason below and raise a complaint with the OMC.</span>
          </label>
        </Section>
        <Section title="Remarks"><textarea v-model="d.remarks" class="inp h-20 py-2" :disabled="!ed" /></Section>
      </div>

      <div class="space-y-4">
        <Section title="Totals">
          <div class="space-y-3">
            <AutoField label="Invoice qty" :value="litres(d.total_invoice_qty)" />
            <AutoField label="Received qty" :value="litres(d.total_received_qty)" />
            <AutoField label="Short / excess" :value="litres(d.total_shortage_qty)" :tone="d.total_shortage_qty > 0.5 ? 'bad' : 'good'" big />
            <AutoField label="Invoice amount" :value="inr(d.total_amount)" />
          </div>
          <div v-if="f.serverError.value && ed && d.items.every((r) => r.tank && r.invoice_qty)" class="mt-3 flex gap-2 rounded-lg bg-amber-50 px-3 py-2 text-[12px] text-amber-800">
            <i class="lucide-triangle-alert mt-0.5 size-4 shrink-0" />{{ f.serverError.value }}
          </div>
        </Section>
        <Section v-if="f.full.value?.linked?.length" title="Posted to ERPNext" flush>
          <a v-for="l in f.full.value.linked" :key="l.name" :href="deskUrl(l.doctype, l.name)" target="_blank" class="flex justify-between border-b border-line px-4 py-2 text-[12px] hover:bg-gray-50">
            <span><b>{{ l.doctype }}</b> {{ l.purpose || '' }}<br /><span class="text-ink-3">{{ l.name }}</span></span><span class="num">{{ l.grand_total ? inr(l.grand_total) : '' }}</span>
          </a>
        </Section>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useDocForm, nextKey } from '../composables/useDocForm'
import { api, getList, deskUrl } from '../api'
import { session } from '../session'
import { inr, num, litres, dateFmt, today, flt } from '../format'
import PageHeader from '../components/PageHeader.vue'
import Section from '../components/Section.vue'
import Field from '../components/Field.vue'
import AutoField from '../components/AutoField.vue'
import NumInput from '../components/NumInput.vue'
import LinkInput from '../components/LinkInput.vue'
import FuelChip from '../components/FuelChip.vue'
import EmployeeSelect from '../components/EmployeeSelect.vue'
import StatusPill from '../components/StatusPill.vue'
import FormActions from '../components/FormActions.vue'
import Toggle from '../components/Toggle.vue'

const props = defineProps({ name: String })
const tanks = ref([])
const nowTime = () => new Date().toTimeString().slice(0, 8)
const f = useDocForm({
  doctype: 'Tanker Receipt', name: props.name, route: '/tankers', tables: ['items'],
  blank: async () => ({ doctype: 'Tanker Receipt', station: session.station, posting_date: today(), posting_time: nowTime(),
    supplier: (await getList('Supplier', { fields: ['name'], limit_page_length: 1, filters: { supplier_name: ['like', '%Oil%'] } }))[0]?.name || '',
    received_by: session.boot.employee?.name || '', seals_intact: 1, sales_stopped: 1, water_checked: 1, override_density_check: 0,
    items: [{ tank: '', invoice_qty: 0, rate: 0 }] }),
})
const d = computed(() => f.doc.value)
const ed = computed(() => f.editable.value)
const tol = computed(() => flt(session.boot.settings?.density_tolerance) || 3)
const densityOk = (r) => Math.abs(flt(r.density_at_15) - flt(r.challan_density)) <= tol.value
const hasDensityFail = computed(() => d.value.items.some((r) => r.challan_density && r.density_at_15 && !densityOk(r)))
const blocked = computed(() => (hasDensityFail.value && !d.value.override_density_check) || (!d.value.seals_intact && !d.value.remarks))
const blockReason = computed(() => (hasDensityFail.value && !d.value.override_density_check ? 'Density outside tolerance' : 'Seals not intact: add remarks'))

function addItem() { d.value.items.push({ tank: '', invoice_qty: 0, rate: 0, _key: nextKey() }) }
async function onTank(r) {
  const t = tanks.value.find((x) => x.name === r.tank)
  r.fuel_item = t?.fuel_item
  if (!r.rate && r.fuel_item) {
    const it = await getList('Item', { filters: { name: r.fuel_item }, fields: ['last_purchase_rate', 'valuation_rate'] })
    r.rate = flt(it[0]?.last_purchase_rate || it[0]?.valuation_rate)
  }
  calc()
}
function calc() {
  d.value.items.forEach((r) => { r.amount = flt(flt(r.invoice_qty) * flt(r.rate)) })
  if (!ed.value) return
  f.schedule((sd) => {
    sd.items.forEach((s, i) => {
      const r = d.value.items[i]
      if (!r) return
      Object.assign(r, { stock_before: s.stock_before, stock_after: s.stock_after, received_qty: s.received_qty, shortage_qty: s.shortage_qty,
        density_variance: s.density_variance, density_ok: s.density_ok, fuel_item: s.fuel_item || r.fuel_item })
    })
    for (const k of ['total_invoice_qty', 'total_received_qty', 'total_shortage_qty', 'total_amount']) d.value[k] = sd[k]
  }, 400)
}
onMounted(async () => {
  tanks.value = await getList('Fuel Tank Master', { filters: { station: session.station, status: 'Active' }, fields: ['name', 'fuel_item'], order_by: 'name' })
  await f.load()
})
</script>
