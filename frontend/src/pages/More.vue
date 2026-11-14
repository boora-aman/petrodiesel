<template>
  <div>
    <PageHeader title="More" />
    <div class="card divide-y divide-line">
      <RouterLink v-for="i in items" :key="i.to" :to="i.to" class="flex items-center gap-3 px-4 py-3.5 text-[14px] font-medium">
        <i :class="i.icon" class="size-5 text-brand-600" />{{ i.label }}<i class="lucide-chevron-right ml-auto size-4 text-ink-3" />
      </RouterLink>
      <a href="/assets/petrodiesel/docs/PetroDesk-User-Guide.pdf" target="_blank" class="flex items-center gap-3 px-4 py-3.5 text-[14px] font-medium"><i class="lucide-book-open size-5 text-brand-600" />User guide (PDF)<i class="lucide-external-link ml-auto size-4 text-ink-3" /></a>
      <a href="/desk" class="flex items-center gap-3 px-4 py-3.5 text-[14px] font-medium"><i class="lucide-layout-grid size-5 text-brand-600" />ERPNext Desk<i class="lucide-external-link ml-auto size-4 text-ink-3" /></a>
      <button class="flex w-full items-center gap-3 px-4 py-3.5 text-[14px] font-medium text-red-600" @click="logout"><i class="lucide-log-out size-5" />Log out</button>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import { session, can, logout } from '../session'
import PageHeader from '../components/PageHeader.vue'
const mgr = computed(() => ['owner', 'manager'].includes(session.boot.view))
const items = computed(() => [
  session.boot.view !== 'stock' && can('Shift Sale Entry', 'read') && { label: 'Shift closing', to: '/shifts', icon: 'lucide-receipt-indian-rupee' },
  can('Tanker Receipt', 'read') && { label: 'Tanker receipts', to: '/tankers', icon: 'lucide-truck' },
  can('Tank Dip Reading', 'read') && { label: 'Tank dips', to: '/dips', icon: 'lucide-ruler' },
  can('Daily Stock Register', 'read') && { label: 'Daily stock register', to: '/dsr', icon: 'lucide-notebook-tabs' },
  can('Pump Test Log', 'read') && { label: 'Pump tests', to: '/pump-tests', icon: 'lucide-flask-conical' },
  can('Fuel Price Update', 'read') && { label: 'Fuel prices', to: '/prices', icon: 'lucide-tag' },
  session.boot.view !== 'stock' && can('Customer', 'read') && { label: 'Credit customers', to: '/credit', icon: 'lucide-users' },
  session.boot.view !== 'stock' && can('Credit Bill', 'read') && { label: 'Credit bills', to: '/credit-bills', icon: 'lucide-file-text' },
  session.boot.view !== 'stock' && can('Staff Advance', 'read') && { label: 'Staff advances', to: '/advances', icon: 'lucide-hand-coins' },
  can('Shop Purchase', 'read') && { label: 'Shop purchases', to: '/purchases', icon: 'lucide-shopping-cart' },
  can('Internal Stock Transfer', 'read') && { label: 'Stock transfers', to: '/transfers', icon: 'lucide-arrow-left-right' },
  { label: 'Reports', to: '/reports', icon: 'lucide-chart-column' },
  mgr.value && { label: 'Approvals', to: '/approvals', icon: 'lucide-badge-check' },
  { label: 'Alerts', to: '/alerts', icon: 'lucide-bell' },
  mgr.value && { label: 'Outlet setup', to: '/setup', icon: 'lucide-settings' },
].filter(Boolean))
</script>
