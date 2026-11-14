<template>
  <div>
    <PageHeader title="Staff advances" subtitle="Money given to staff and how much is still to recover">
      <template #actions>
        <button v-if="can('Staff Advance Recovery', 'create')" class="btn-secondary" @click="openRecover()"><i class="lucide-undo-2 size-4" />Record recovery</button>
        <button v-if="can('Staff Advance', 'create')" class="btn-primary" @click="openGive()"><i class="lucide-plus size-4" />Give advance</button>
      </template>
    </PageHeader>
    <div class="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
      <KpiCard label="Outstanding with staff" :value="inr(totals.balance, true)" :loading="loading" />
      <KpiCard label="Given (all time)" :value="inr(totals.given, true)" :loading="loading" />
      <KpiCard label="Recovered (all time)" :value="inr(totals.recovered, true)" :loading="loading" />
      <KpiCard label="Staff with balance" :value="String(balances.filter((b) => b.balance > 0.5).length)" :loading="loading" />
    </div>
    <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <Section title="Balance by employee" flush class="xl:col-span-2">
        <EmptyState v-if="!loading && !balances.length" title="No advances yet" icon="lucide-wallet" />
        <div v-else class="overflow-x-auto">
          <table class="tbl">
            <thead><tr><th>Employee</th><th class="!text-right">Given</th><th class="!text-right">Recovered</th><th class="!text-right">Balance</th><th>Last entry</th><th /></tr></thead>
            <tbody>
              <tr v-for="b in balances" :key="b.employee" class="cursor-pointer" @click="showLedger(b)">
                <td class="font-medium">{{ b.employee_name }}</td><td class="r">{{ inr(b.given) }}</td><td class="r">{{ inr(b.recovered) }}</td>
                <td class="r font-semibold" :class="b.balance > 0.5 ? 'text-amber-700' : 'text-green-700'">{{ inr(b.balance) }}</td>
                <td>{{ dateFmt(b.last_date) }}</td>
                <td class="text-right"><button v-if="b.balance > 0.5 && can('Staff Advance Recovery', 'create')" class="btn-secondary btn-sm" @click.stop="openRecover(b)">Recover</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>
      <div class="space-y-4">
        <Section title="Recent advances" flush>
          <div class="divide-y divide-line">
            <div v-for="r in recent" :key="r.name" class="flex justify-between px-4 py-2 text-[12px]">
              <span><b>{{ r.employee_name }}</b><br /><span class="text-ink-3">{{ dateFmt(r.posting_date) }} · {{ r.recovery_method }} · {{ ['Draft', 'Submitted', 'Cancelled'][r.docstatus] }}</span></span>
              <span class="num font-medium">{{ inr(r.amount) }}</span>
            </div>
            <EmptyState v-if="!recent.length" title="None" />
          </div>
        </Section>
        <Section title="Recent recoveries" flush>
          <div class="divide-y divide-line">
            <div v-for="r in recoveries" :key="r.name" class="flex justify-between px-4 py-2 text-[12px]">
              <span><b>{{ r.employee_name }}</b><br /><span class="text-ink-3">{{ dateFmt(r.posting_date) }} · {{ r.method }}</span></span>
              <span class="num font-medium text-green-700">{{ inr(r.amount) }}</span>
            </div>
            <EmptyState v-if="!recoveries.length" title="None" />
          </div>
        </Section>
      </div>
    </div>

    <Modal v-model="give.open" title="Give advance">
      <div class="space-y-3">
        <Field label="Employee" required><EmployeeSelect v-model="give.employee" /></Field>
        <div class="grid grid-cols-2 gap-3">
          <Field label="Amount" required><NumInput v-model="give.amount" big /></Field>
          <Field label="Date"><input v-model="give.posting_date" type="date" class="inp" /></Field>
        </div>
        <Field label="Paid by"><select v-model="give.mode_of_payment" class="inp"><option v-for="m in ['Cash', ...(session.boot.payment_modes || [])]" :key="m">{{ m }}</option></select></Field>
        <div class="grid grid-cols-2 gap-3">
          <Field label="Recover by"><select v-model="give.recovery_method" class="inp"><option>Salary Deduction</option><option>Cash Return</option></select></Field>
          <Field label="Monthly instalments"><NumInput v-model="give.installments" /></Field>
        </div>
        <Field label="Purpose"><input v-model="give.purpose" class="inp" placeholder="e.g. medical, festival" /></Field>
      </div>
      <template #footer><button class="btn-secondary" @click="give.open = false">Close</button><button class="btn-primary" :disabled="busy || !give.employee || !give.amount" @click="submitGive">Give {{ give.amount ? inr(give.amount) : '' }}</button></template>
    </Modal>

    <Modal v-model="rec.open" title="Record recovery">
      <div class="space-y-3">
        <Field label="Employee" required><EmployeeSelect v-model="rec.employee" @change="loadOutstanding" /></Field>
        <AutoField label="Outstanding" :value="inr(rec.outstanding)" />
        <div class="grid grid-cols-2 gap-3">
          <Field label="Amount" required :error="rec.amount > rec.outstanding + 0.01 ? 'More than outstanding' : ''"><NumInput v-model="rec.amount" big /></Field>
          <Field label="Date"><input v-model="rec.posting_date" type="date" class="inp" /></Field>
        </div>
        <div class="flex gap-2">
          <button v-for="m in ['Cash Return', 'Salary Deduction']" :key="m" class="flex-1 rounded-lg border px-3 py-2 text-[13px] font-medium" :class="rec.method === m ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-line'" @click="rec.method = m">{{ m }}</button>
        </div>
        <Field v-if="rec.method === 'Cash Return'" label="Received in"><select v-model="rec.mode_of_payment" class="inp"><option v-for="m in ['Cash', ...(session.boot.payment_modes || [])]" :key="m">{{ m }}</option></select></Field>
        <Field v-else label="Deduct in payroll of" hint="Creates an Additional Salary deduction in HR payroll"><input v-model="rec.payroll_date" type="date" class="inp" /></Field>
        <Field label="Remarks"><input v-model="rec.remarks" class="inp" /></Field>
      </div>
      <template #footer><button class="btn-secondary" @click="rec.open = false">Close</button><button class="btn-primary" :disabled="busy || !rec.employee || !rec.amount || rec.amount > rec.outstanding + 0.01" @click="submitRec">Record {{ rec.amount ? inr(rec.amount) : '' }}</button></template>
    </Modal>

    <Modal v-model="ledger.open" :title="`${ledger.name} — advance ledger`" width="sm:max-w-3xl">
      <div class="overflow-x-auto">
        <table class="tbl"><thead><tr><th>Date</th><th>Entry</th><th class="!text-right">Given</th><th class="!text-right">Recovered</th><th class="!text-right">Balance</th><th>Remarks</th></tr></thead>
          <tbody><tr v-for="(r, i) in ledger.rows" :key="i"><td>{{ dateFmt(r.posting_date) }}</td><td class="text-[12px]">{{ r.voucher_type }}<br /><span class="text-ink-3">{{ r.voucher_no }}</span></td>
            <td class="r">{{ r.given ? inr(r.given) : '' }}</td><td class="r text-green-700">{{ r.recovered ? inr(r.recovered) : '' }}</td><td class="r font-semibold">{{ inr(r.balance) }}</td><td class="wrap min-w-48 text-[12px]">{{ r.remarks }}</td></tr></tbody></table>
      </div>
    </Modal>
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { toast } from 'frappe-ui'
import { api, errorText } from '../api'
import { session, can } from '../session'
import { inr, dateFmt, today } from '../format'
import PageHeader from '../components/PageHeader.vue'
import Section from '../components/Section.vue'
import KpiCard from '../components/KpiCard.vue'
import Field from '../components/Field.vue'
import AutoField from '../components/AutoField.vue'
import NumInput from '../components/NumInput.vue'
import Modal from '../components/Modal.vue'
import EmptyState from '../components/EmptyState.vue'
import EmployeeSelect from '../components/EmployeeSelect.vue'

const loading = ref(true)
const busy = ref(false)
const balances = ref([])
const recent = ref([])
const recoveries = ref([])
const give = reactive({ open: false })
const rec = reactive({ open: false })
const ledger = reactive({ open: false, name: '', rows: [] })
const totals = computed(() => balances.value.reduce((a, b) => ({ given: a.given + b.given, recovered: a.recovered + b.recovered, balance: a.balance + b.balance }), { given: 0, recovered: 0, balance: 0 }))
async function load() {
  loading.value = true
  try { const r = await api('advances_overview'); balances.value = r.balances; recent.value = r.recent; recoveries.value = r.recoveries }
  catch (e) { toast.error(errorText(e)) } finally { loading.value = false }
}
function openGive() { Object.assign(give, { open: true, employee: '', amount: 0, posting_date: today(), mode_of_payment: 'Cash', recovery_method: 'Salary Deduction', installments: 1, purpose: '' }) }
function openRecover(b) {
  Object.assign(rec, { open: true, employee: b?.employee || '', outstanding: b?.balance || 0, amount: b?.balance || 0, posting_date: today(),
    method: 'Cash Return', mode_of_payment: 'Cash', payroll_date: today().slice(0, 8) + '01', remarks: '' })
}
async function loadOutstanding() { rec.outstanding = rec.employee ? await api('petrodiesel.petrodiesel.advances.get_outstanding', { employee: rec.employee }) : 0; rec.amount = rec.outstanding }
async function submitGive() {
  busy.value = true
  try {
    await api('save_doc', { doc: { doctype: 'Staff Advance', station: session.station, ...pick(give, ['employee', 'amount', 'posting_date', 'mode_of_payment', 'recovery_method', 'installments', 'purpose']) }, action: 'submit' })
    toast.success('Advance given and posted'); give.open = false; load()
  } catch (e) { toast.error(errorText(e)) } finally { busy.value = false }
}
async function submitRec() {
  busy.value = true
  try {
    await api('save_doc', { doc: { doctype: 'Staff Advance Recovery', station: session.station, ...pick(rec, ['employee', 'amount', 'posting_date', 'method', 'mode_of_payment', 'payroll_date', 'remarks']) }, action: 'submit' })
    toast.success(rec.method === 'Salary Deduction' ? 'Deduction added to payroll' : 'Recovery recorded'); rec.open = false; load()
  } catch (e) { toast.error(errorText(e)) } finally { busy.value = false }
}
async function showLedger(b) {
  Object.assign(ledger, { open: true, name: b.employee_name, rows: await api('petrodiesel.petrodiesel.advances.get_employee_ledger', { employee: b.employee }) })
}
const pick = (o, keys) => Object.fromEntries(keys.map((k) => [k, o[k]]))
onMounted(load)
</script>
