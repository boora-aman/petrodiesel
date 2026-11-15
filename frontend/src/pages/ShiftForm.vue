<template>
	<div v-if="doc">
		<PageHeader
			:title="isNew ? 'New shift closing' : doc.name"
			back="/shifts"
			:subtitle="`${doc.shift || 'Select shift'} · ${dateFmt(doc.posting_date)} · ${
				doc.cashier_name || 'No cashier'
			}`"
		>
			<template #badge><StatusPill :status="stateLabel" /></template>
			<template #actions>
				<a
					v-if="!isNew"
					:href="printUrl('Shift Sale Entry', doc.name, 'Shift Closing Report')"
					target="_blank"
					class="btn-secondary"
					><i class="lucide-printer size-4" /><span class="hidden sm:inline"
						>Print</span
					></a
				>
				<button v-if="editable" class="btn-secondary" :disabled="busy" @click="save()">
					<i class="lucide-save size-4" />Save draft
				</button>
				<button
					v-if="editable && submitAction"
					class="btn-primary"
					:disabled="busy"
					@click="save(submitAction)"
				>
					<i class="lucide-send size-4" />{{
						submitAction === "submit" ? "Submit & post" : "Submit for approval"
					}}
				</button>
				<template v-for="t in otherTransitions" :key="t">
					<button
						:class="
							t === 'Reject' || t === 'Cancel'
								? 'btn-secondary !text-red-600'
								: 'btn-primary'
						"
						:disabled="busy"
						@click="transition(t)"
					>
						{{ t }}
					</button>
				</template>
			</template>
		</PageHeader>

		<!-- Sticky live summary -->
		<div
			class="sticky top-14 z-10 -mx-4 mb-4 border-y border-line bg-white/95 px-4 py-2 backdrop-blur lg:-mx-6 lg:px-6"
		>
			<div class="flex flex-wrap items-center gap-x-5 gap-y-1 text-[12px]">
				<span class="pill text-[12px]" :class="cashTone.cls"
					><span class="size-1.5 rounded-full" :class="cashTone.dot" />{{
						cashTone.label
					}}</span
				>
				<span
					>Sale <b class="num">{{ litres(t.total_sale_qty) }}</b></span
				>
				<span
					>Gross <b class="num">{{ inr(t.gross_sales) }}</b></span
				>
				<span
					>Expected cash <b class="num">{{ inr(t.expected_cash) }}</b></span
				>
				<span
					>Counted <b class="num">{{ inr(t.cash_counted) }}</b></span
				>
				<span v-if="previewing" class="text-ink-3"
					><i class="lucide-loader-circle inline size-3 animate-spin" /> checking…</span
				>
				<button
					v-else-if="serverError && editable"
					class="flex min-w-0 max-w-full items-center gap-1 text-amber-700 sm:max-w-md"
					:title="serverError"
					@click="step = 4"
				>
					<i class="lucide-triangle-alert size-3.5 shrink-0" /><span
						class="line-clamp-2 text-left"
						>{{ serverError }}</span
					>
				</button>
			</div>
		</div>

		<!-- Header fields -->
		<div class="card card-pad mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
			<Field label="Business date" required
				><input
					v-model="doc.posting_date"
					type="date"
					class="inp"
					:disabled="!editable"
					@change="onHeader"
			/></Field>
			<Field label="Shift" required :hint="shiftHours">
				<select v-model="doc.shift" class="inp" :disabled="!editable" @change="onHeader">
					<option value="" disabled>Select</option>
					<option v-for="s in session.boot.shifts" :key="s.name" :value="s.name">
						{{ s.name }}
					</option>
					<option
						v-if="doc.shift && !session.boot.shifts.some((x) => x.name === doc.shift)"
						:value="doc.shift"
					>
						{{ doc.shift }}
					</option>
				</select>
			</Field>
			<Field label="Cashier / in-charge" class="col-span-2 md:col-span-1"
				><EmployeeSelect v-model="doc.cashier" :disabled="!editable" @change="schedule"
			/></Field>
			<AutoField label="Outlet" :value="session.boot.station?.station_name" />
		</div>

		<!-- Steps -->
		<div class="no-scrollbar mb-4 flex gap-1 overflow-x-auto border-b border-line">
			<button
				v-for="(s, i) in steps"
				:key="s.key"
				:ref="(el) => (tabEls[i] = el)"
				class="tab-btn flex items-center gap-1.5"
				:class="{ active: step === i }"
				@click="step = i"
			>
				<span
					class="flex size-5 items-center justify-center rounded-full text-[10px] font-semibold"
					:class="step === i ? 'bg-brand-600 text-white' : 'bg-slate-100 text-ink-2'"
					>{{ i + 1 }}</span
				>
				{{ s.label }}
				<span v-if="s.count" class="text-[11px] text-ink-3">({{ s.count }})</span>
			</button>
		</div>

		<!-- STEP 1: meter readings -->
		<div v-show="step === 0" class="space-y-4">
			<div class="flex flex-wrap items-center gap-2">
				<button v-if="editable" class="btn-primary" :disabled="busy" @click="loadNozzles">
					<i class="lucide-download size-4" />Load active nozzles
				</button>
				<span class="text-[12px] text-ink-3"
					>Opening readings come from the last closing. Enter the closing totalizer and
					test litres.</span
				>
			</div>
			<EmptyState
				v-if="!doc.nozzle_readings.length"
				title="No nozzles loaded"
				text="Tap “Load active nozzles” to start."
				icon="lucide-fuel"
			/>
			<Section v-for="g in groups" :key="g.du" :title="g.du" flush>
				<template v-if="editable" #actions>
					<div
						v-for="side in g.sides"
						:key="side"
						class="flex items-center gap-1.5 text-[12px] text-ink-2"
					>
						<span class="whitespace-nowrap">Side {{ side || "—" }}</span>
						<div class="w-40">
							<EmployeeSelect
								:model-value="sideAttendant(g, side)"
								placeholder="Attendant"
								@change="(v) => setSide(g, side, v)"
							/>
						</div>
					</div>
				</template>
				<div class="divide-y divide-line">
					<div v-for="r in g.rows" :key="r._key" class="px-4 py-3">
						<div class="mb-2 flex flex-wrap items-center gap-2">
							<FuelChip :item="r.fuel_item" />
							<span class="text-[15px] font-semibold">{{ r.nozzle }}</span>
							<span class="text-[12px] text-ink-3"
								>{{ r.tank }} · side {{ nozzleSide[r.nozzle] || "—" }}</span
							>
							<span
								v-if="r._priceRow"
								class="pill border-blue-200 bg-blue-50 text-blue-700"
								>Price change row</span
							>
							<div class="ml-auto w-full sm:w-56">
								<EmployeeSelect
									v-model="r.attendant"
									:disabled="!editable"
									placeholder="Attendant (DSM)"
								/>
							</div>
						</div>
						<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-7">
							<AutoField label="Opening" :value="num(r.opening_reading)" />
							<div class="col-span-2 sm:col-span-2">
								<Field
									label="Closing reading"
									:error="
										r.closing_reading < r.opening_reading
											? 'Below opening reading'
											: ''
									"
								>
									<NumInput
										v-model="r.closing_reading"
										big
										:disabled="!editable"
										:invalid="r.closing_reading < r.opening_reading"
										@update:model-value="recalc"
									/>
								</Field>
							</div>
							<Field label="Test (L)">
								<div class="flex gap-1">
									<NumInput
										v-model="r.test_qty"
										:disabled="!editable"
										@update:model-value="recalc"
									/>
									<button
										v-if="editable"
										class="btn-secondary !px-2 text-[11px]"
										title="Add 5 L test"
										@click="
											r.test_qty = flt((r.test_qty || 0) + 5);
											recalc();
										"
									>
										+5
									</button>
								</div>
							</Field>
							<AutoField
								label="Sale (L)"
								:value="num(r.sale_qty)"
								:tone="r.sale_qty < 0 ? 'bad' : ''"
							/>
							<Field v-if="r._priceRow" label="Rate"
								><NumInput
									v-model="r.rate"
									:disabled="!editable"
									@update:model-value="recalc"
							/></Field>
							<AutoField v-else label="Rate" :value="num(r.rate)" />
							<AutoField label="Amount" :value="num(r.amount)" />
						</div>
						<div v-if="editable" class="mt-2 flex gap-3 text-[12px]">
							<button
								v-if="!r._priceRow"
								class="text-brand-600 hover:underline"
								@click="addPriceRow(r)"
							>
								+ Price change row
							</button>
							<button
								v-else
								class="text-red-600 hover:underline"
								@click="removeRow('nozzle_readings', r)"
							>
								Remove row
							</button>
						</div>
					</div>
				</div>
			</Section>

			<Section v-if="fuelSummary.length" title="Fuel-wise summary" flush>
				<div class="overflow-x-auto">
					<div class="overflow-x-auto">
						<table class="tbl">
							<thead>
								<tr>
									<th>Fuel</th>
									<th class="!text-right">Meter</th>
									<th class="!text-right">Test</th>
									<th class="!text-right">Sale</th>
									<th class="!text-right">Credit</th>
									<th class="!text-right">Retail</th>
									<th class="!text-right">Amount</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="f in fuelSummary" :key="f.fuel_item">
									<td><FuelChip :item="f.fuel_item" /></td>
									<td class="r">{{ num(f.meter_qty) }}</td>
									<td class="r">{{ num(f.test_qty) }}</td>
									<td class="r font-semibold">{{ num(f.sale_qty) }}</td>
									<td class="r">{{ num(f.credit_qty) }}</td>
									<td class="r">{{ num(f.retail_qty) }}</td>
									<td class="r">{{ inr(f.amount) }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</Section>
		</div>

		<!-- STEP 2: credit and other sales -->
		<div v-show="step === 1" class="space-y-4">
			<Section
				title="Credit sales (indent / slip)"
				subtitle="Fuel given on credit to fleet customers"
			>
				<template #actions
					><button
						v-if="editable"
						class="btn-secondary btn-sm"
						@click="addRow('credit_sales', { fuel_item: defaultFuel() })"
					>
						<i class="lucide-plus size-3.5" />Add slip
					</button></template
				>
				<EmptyState
					v-if="!doc.credit_sales.length"
					title="No credit slips"
					icon="lucide-file-text"
				/>
				<div class="space-y-3">
					<div
						v-for="r in doc.credit_sales"
						:key="r._key"
						class="rounded-lg border border-line p-3"
						:class="limitOf(r.customer)?.over ? '!border-red-300 bg-red-50/40' : ''"
					>
						<div class="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:grid-cols-12">
							<div class="col-span-2 xl:col-span-3">
								<Field label="Customer" required
									><LinkInput
										v-model="r.customer"
										doctype="Customer"
										:disabled="!editable"
										@change="
											r.vehicle = '';
											recalc();
										"
								/></Field>
							</div>
							<div class="col-span-2 xl:col-span-2">
								<Field label="Vehicle"
									><LinkInput
										v-model="r.vehicle"
										doctype="Customer Vehicle"
										:filters="
											r.customer
												? { customer: r.customer, is_active: 1 }
												: { is_active: 1 }
										"
										:disabled="!editable"
										@change="onVehicle(r)"
								/></Field>
							</div>
							<div class="xl:col-span-1">
								<Field label="Slip no"
									><input v-model="r.slip_no" class="inp" :disabled="!editable"
								/></Field>
							</div>
							<div class="col-span-2 xl:col-span-2">
								<Field label="Filled by"
									><select
										v-model="r.attendant"
										class="inp !pl-2 !pr-7"
										:disabled="!editable"
										@change="recalc"
									>
										<option value="">—</option>
										<option v-for="p in shiftPeople" :key="p" :value="p">
											{{ empName(p) }}
										</option>
									</select></Field
								>
							</div>
							<div class="xl:col-span-1">
								<Field label="Fuel"
									><select
										v-model="r.fuel_item"
										class="inp !pl-2 !pr-7"
										:disabled="!editable"
										@change="setCreditRate(r)"
									>
										<option
											v-for="f in session.boot.fuels"
											:key="f.name"
											:value="f.name"
										>
											{{ f.name }}
										</option>
									</select></Field
								>
							</div>
							<div class="xl:col-span-1">
								<Field label="Qty (L)"
									><NumInput
										v-model="r.qty"
										:disabled="!editable"
										@update:model-value="recalc"
								/></Field>
							</div>
							<div class="xl:col-span-1">
								<AutoField label="Rate" :value="num(r.rate)" />
							</div>
							<div class="xl:col-span-2">
								<AutoField label="Amount" :value="inr(r.amount)" />
							</div>
						</div>
						<div class="mt-2 flex flex-wrap items-center gap-3 text-[12px]">
							<span v-if="r.driver_name" class="text-ink-2"
								>Driver: {{ r.driver_name }}</span
							>
							<template v-if="limitOf(r.customer)">
								<div class="h-1.5 w-32 overflow-hidden rounded-full bg-slate-100">
									<div
										class="h-full"
										:class="
											limitOf(r.customer).over
												? 'bg-red-600'
												: limitOf(r.customer).pct > 80
												? 'bg-amber-500'
												: 'bg-green-600'
										"
										:style="{
											width: Math.min(limitOf(r.customer).pct, 100) + '%',
										}"
									/>
								</div>
								<span
									:class="
										limitOf(r.customer).over
											? 'font-semibold text-red-600'
											: 'text-ink-2'
									"
									>{{ limitOf(r.customer).text }}</span
								>
							</template>
							<button
								v-if="editable"
								class="ml-auto text-red-600 hover:underline"
								@click="removeRow('credit_sales', r)"
							>
								Remove
							</button>
						</div>
					</div>
				</div>
			</Section>

			<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
				<Section title="Lubricant & shop sales" subtitle="GST 18% inclusive">
					<template #actions
						><button
							v-if="editable"
							class="btn-secondary btn-sm"
							@click="addRow('other_sales', { qty: 1 })"
						>
							<i class="lucide-plus size-3.5" />Add item
						</button></template
					>
					<EmptyState
						v-if="!doc.other_sales.length"
						title="No lube sales"
						icon="lucide-droplet"
					/>
					<div
						v-for="r in doc.other_sales"
						:key="r._key"
						class="mb-2 grid grid-cols-12 items-end gap-2"
					>
						<div class="col-span-12 sm:col-span-5">
							<Field label="Item"
								><LinkInput
									v-model="r.item_code"
									doctype="Item"
									:filters="{
										petro_product_type: [
											'in',
											['Lubricant', 'Accessory', 'Other'],
										],
									}"
									:disabled="!editable"
									@change="onItem(r)"
							/></Field>
						</div>
						<div class="col-span-3 sm:col-span-2">
							<Field label="Qty"
								><NumInput
									v-model="r.qty"
									:disabled="!editable"
									@update:model-value="recalc"
							/></Field>
						</div>
						<div class="col-span-4 sm:col-span-2">
							<Field label="Rate"
								><NumInput
									v-model="r.rate"
									:disabled="!editable"
									@update:model-value="recalc"
							/></Field>
						</div>
						<div class="col-span-4 sm:col-span-2">
							<AutoField label="Amount" :value="num(r.amount)" />
						</div>
						<button
							v-if="editable"
							class="col-span-1 pb-2 text-red-600"
							@click="removeRow('other_sales', r)"
						>
							<i class="lucide-trash-2 size-4" />
						</button>
					</div>
				</Section>
				<Section
					title="Cash paid to fleet drivers"
					subtitle="Billed to the customer's account"
				>
					<template #actions
						><button
							v-if="editable"
							class="btn-secondary btn-sm"
							@click="addRow('driver_cash', {})"
						>
							<i class="lucide-plus size-3.5" />Add
						</button></template
					>
					<EmptyState
						v-if="!doc.driver_cash.length"
						title="No driver cash"
						icon="lucide-banknote"
					/>
					<div
						v-for="r in doc.driver_cash"
						:key="r._key"
						class="mb-2 grid grid-cols-12 items-end gap-2"
					>
						<div class="col-span-12 sm:col-span-4">
							<Field label="Customer"
								><LinkInput
									v-model="r.customer"
									doctype="Customer"
									:disabled="!editable"
							/></Field>
						</div>
						<div class="col-span-6 sm:col-span-3">
							<Field label="Vehicle"
								><LinkInput
									v-model="r.vehicle"
									doctype="Customer Vehicle"
									:filters="r.customer ? { customer: r.customer } : {}"
									:disabled="!editable"
							/></Field>
						</div>
						<div class="col-span-5 sm:col-span-4">
							<Field label="Amount"
								><NumInput
									v-model="r.amount"
									:disabled="!editable"
									@update:model-value="recalc"
							/></Field>
						</div>
						<button
							v-if="editable"
							class="col-span-1 pb-2 text-red-600"
							@click="removeRow('driver_cash', r)"
						>
							<i class="lucide-trash-2 size-4" />
						</button>
					</div>
				</Section>
			</div>
		</div>

		<!-- STEP 3: collections -->
		<div v-show="step === 2" class="space-y-4">
			<Section
				title="Attendant-wise collection"
				subtitle="For each attendant: his nozzles' sales − his credit slips − his UPI / card / fleet = cash he must hand over"
				flush
			>
				<EmptyState
					v-if="!attRows.length"
					title="No attendants on the nozzles yet"
					text="Go to Meter readings and choose the attendant for each side or nozzle."
					icon="lucide-users"
				/>
				<div class="divide-y divide-line">
					<div v-for="a in attRows" :key="a.attendant" class="p-4">
						<div class="mb-3 flex flex-wrap items-center gap-2">
							<span
								class="flex size-8 items-center justify-center rounded-full bg-brand-600 text-[12px] font-semibold text-white"
								>{{ initials(empName(a.attendant)) }}</span
							>
							<div class="min-w-0">
								<div class="text-[15px] font-semibold">
									{{ empName(a.attendant) }}
								</div>
								<div class="text-[12px] text-ink-3">Nozzles {{ a.nozzles }}</div>
							</div>
						</div>
						<div class="mb-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
							<AutoField label="Sale value" :value="inr(a.sale_amount)" />
							<AutoField label="His credit slips" :value="inr(a.credit_amount)" />
							<AutoField
								label="His UPI / card / fleet"
								:value="inr(a.digital_amount)"
							/>
							<AutoField
								label="Cash he must hand over"
								:value="inr(a.expected_cash)"
							/>
						</div>
						<div class="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-5">
							<Field v-for="mode in modes" :key="mode" :label="mode">
								<NumInput
									:model-value="payment(mode, a.attendant).amount"
									:disabled="!editable"
									placeholder="0"
									@update:model-value="
										setPayment(mode, a.attendant, 'amount', $event)
									"
								/>
							</Field>
							<Field label="Cash handed over">
								<NumInput
									v-model="a.cash_handed"
									:disabled="!editable"
									placeholder="0"
									@update:model-value="recalc"
								/>
							</Field>
						</div>
						<div class="mt-2 flex items-center justify-end gap-2 text-[13px]">
							<span class="text-ink-2"
								>{{ empName(a.attendant) }}'s short / excess</span
							>
							<span
								v-if="a.cash_handed"
								class="num font-semibold"
								:class="
									a.short_excess < -0.5
										? 'text-red-600'
										: a.short_excess > 0.5
										? 'text-amber-600'
										: 'text-green-700'
								"
								>{{ signedInr(a.short_excess) }}</span
							>
							<span v-else class="text-ink-3">{{
								editable ? "enter cash handed" : "not recorded"
							}}</span>
						</div>
					</div>
				</div>
			</Section>
			<Section
				v-if="orphanPayments.length"
				title="Unassigned payments"
				subtitle="Collected by someone who is no longer on any nozzle — pick the attendant or remove"
			>
				<div class="space-y-2">
					<div
						v-for="p in orphanPayments"
						:key="p._key"
						class="flex flex-wrap items-center gap-2 text-[13px]"
					>
						<i
							:class="modeIcon(p.mode_of_payment || '')"
							class="size-4 text-brand-600"
						/>
						<span class="font-medium">{{ p.mode_of_payment }}</span>
						<span class="num">{{ inr(p.amount) }}</span>
						<span class="text-ink-3">was {{ empName(p.attendant) }}</span>
						<select
							class="inp !h-8 !w-auto !pl-2 !pr-7 text-[12px]"
							:disabled="!editable"
							value=""
							@change="reassignPayment(p, $event.target.value)"
						>
							<option value="" disabled>Move to…</option>
							<option v-for="who in shiftPeople" :key="who" :value="who">
								{{ empName(who) }}
							</option>
							<option value="__counter">Counter (no attendant)</option>
						</select>
						<button
							v-if="editable"
							class="ml-auto text-red-600 hover:underline"
							@click="removeRow('payments', p)"
						>
							Remove
						</button>
					</div>
				</div>
			</Section>
			<Section
				title="Counter collections (not tied to an attendant)"
				subtitle="e.g. lube / shop counter UPI or card at the cashier"
			>
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
					<div
						v-for="mode in modes"
						:key="mode"
						class="rounded-lg border border-line p-3"
					>
						<div class="mb-2 flex items-center gap-2 text-[13px] font-semibold">
							<i :class="modeIcon(mode)" class="size-4 text-brand-600" />{{ mode }}
						</div>
						<NumInput
							:model-value="payment(mode, '').amount"
							:disabled="!editable"
							placeholder="0"
							@update:model-value="setPayment(mode, '', 'amount', $event)"
						/>
						<input
							:value="payment(mode, '').reference_no"
							class="inp mt-2 h-8 text-[12px]"
							placeholder="Batch / settlement ref"
							:disabled="!editable"
							@input="setPayment(mode, '', 'reference_no', $event.target.value)"
						/>
					</div>
				</div>
				<div class="mt-3 flex justify-end text-[13px]">
					Total digital: <b class="num ml-2">{{ inr(t.digital_amount) }}</b>
				</div>
			</Section>
			<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
				<Section title="Expenses paid from cash">
					<template #actions
						><button
							v-if="editable"
							class="btn-secondary btn-sm"
							@click="addRow('expenses', {})"
						>
							<i class="lucide-plus size-3.5" />Add
						</button></template
					>
					<EmptyState
						v-if="!doc.expenses.length"
						title="No expenses"
						icon="lucide-wallet"
					/>
					<div
						v-for="r in doc.expenses"
						:key="r._key"
						class="mb-2 grid grid-cols-12 items-end gap-2"
					>
						<div class="col-span-12 sm:col-span-5">
							<Field label="Expense head"
								><LinkInput
									v-model="r.expense_account"
									doctype="Account"
									:filters="{ root_type: 'Expense', is_group: 0 }"
									:disabled="!editable"
							/></Field>
						</div>
						<div class="col-span-7 sm:col-span-4">
							<Field label="Description"
								><input v-model="r.description" class="inp" :disabled="!editable"
							/></Field>
						</div>
						<div class="col-span-4 sm:col-span-2">
							<Field label="Amount"
								><NumInput
									v-model="r.amount"
									:disabled="!editable"
									@update:model-value="recalc"
							/></Field>
						</div>
						<button
							v-if="editable"
							class="col-span-1 pb-2 text-red-600"
							@click="removeRow('expenses', r)"
						>
							<i class="lucide-trash-2 size-4" />
						</button>
					</div>
				</Section>
				<Section title="Advances to staff">
					<template #actions
						><button
							v-if="editable"
							class="btn-secondary btn-sm"
							@click="addRow('employee_advances', {})"
						>
							<i class="lucide-plus size-3.5" />Add
						</button></template
					>
					<EmptyState
						v-if="!doc.employee_advances.length"
						title="No advances"
						icon="lucide-user"
					/>
					<div
						v-for="r in doc.employee_advances"
						:key="r._key"
						class="mb-2 grid grid-cols-12 items-end gap-2"
					>
						<div class="col-span-12 sm:col-span-5">
							<Field label="Employee"
								><EmployeeSelect v-model="r.employee" :disabled="!editable"
							/></Field>
						</div>
						<div class="col-span-7 sm:col-span-4">
							<Field label="Remarks"
								><input v-model="r.remarks" class="inp" :disabled="!editable"
							/></Field>
						</div>
						<div class="col-span-4 sm:col-span-2">
							<Field label="Amount"
								><NumInput
									v-model="r.amount"
									:disabled="!editable"
									@update:model-value="recalc"
							/></Field>
						</div>
						<button
							v-if="editable"
							class="col-span-1 pb-2 text-red-600"
							@click="removeRow('employee_advances', r)"
						>
							<i class="lucide-trash-2 size-4" />
						</button>
					</div>
				</Section>
			</div>
		</div>

		<!-- STEP 4: cash count -->
		<div v-show="step === 3" class="grid grid-cols-1 gap-4 lg:grid-cols-2">
			<Section title="Count cash" subtitle="Notes and coins in the drawer">
				<div class="space-y-2">
					<div
						v-for="d in doc.denominations"
						:key="d._key"
						class="flex items-center gap-1.5 sm:gap-2"
					>
						<span
							class="w-14 shrink-0 rounded-md bg-slate-100 px-1 py-1.5 text-center text-[13px] font-semibold"
							>₹{{ d.denomination }}</span
						>
						<button
							class="btn-secondary !h-10 !w-10 shrink-0 !px-0"
							:disabled="!editable || !d.count"
							@click="
								d.count = Math.max((d.count || 0) - 1, 0);
								recalc();
							"
						>
							<i class="lucide-minus size-4" />
						</button>
						<NumInput
							v-model="d.count"
							class="!h-10 w-16 !text-center sm:w-24"
							:disabled="!editable"
							@update:model-value="recalc"
						/>
						<button
							class="btn-primary !h-10 !w-10 shrink-0 !px-0"
							:disabled="!editable"
							@click="
								d.count = (d.count || 0) + 1;
								recalc();
							"
						>
							<i class="lucide-plus size-4" />
						</button>
						<span
							class="num ml-auto whitespace-nowrap text-[13px] font-medium sm:text-[14px]"
							>{{ inr(d.amount, true) }}</span
						>
					</div>
				</div>
				<div
					class="mt-4 flex items-center justify-between rounded-lg bg-brand-50 px-4 py-3"
				>
					<span class="text-[13px] font-medium text-brand-800">Total cash counted</span>
					<span class="num text-[22px] font-semibold text-brand-800">{{
						inr(t.cash_counted)
					}}</span>
				</div>
				<div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
					<AutoField
						label="Opening cash (previous shift)"
						:value="inr(t.opening_float)"
					/>
					<Field label="Leave for next shift"
						><NumInput
							v-model="doc.cash_to_next_shift"
							:disabled="!editable"
							@update:model-value="recalc"
					/></Field>
					<AutoField label="Hand to owner / safe" :value="inr(t.cash_to_safe)" />
				</div>
				<p v-if="t.previous_entry" class="mt-1 text-[11px] text-ink-3">
					Opening cash from {{ t.previous_entry }}.
				</p>
			</Section>
			<Section title="Shift reconciliation">
				<dl class="space-y-1.5 text-[13px]">
					<Row label="Fuel sales" :v="t.fuel_sales_amount" />
					<Row label="+ Lubricant & shop" :v="t.other_sales_amount" />
					<Row label="= Gross sales" :v="t.gross_sales" bold />
					<Row label="− Credit sales" :v="t.credit_sales_amount" />
					<Row
						v-for="p in digitalByMode"
						:key="p.mode"
						:label="`− ${p.mode}`"
						:v="p.amount"
					/>
					<Row label="− Expenses" :v="t.expense_amount" />
					<Row label="− Staff advances" :v="t.advance_amount" />
					<Row label="− Driver cash" :v="t.driver_cash_amount" />
					<Row label="+ Opening cash" :v="t.opening_float" />
					<Row label="= Expected cash in drawer" :v="t.expected_cash" bold />
					<Row label="Cash counted" :v="t.cash_counted" bold />
				</dl>
				<div
					class="mt-3 flex items-center justify-between rounded-lg px-4 py-3"
					:class="cashTone.box"
				>
					<span class="text-[13px] font-semibold">Short (−) / Excess (+)</span>
					<span class="num text-[22px] font-semibold">{{
						signedInr(t.short_excess)
					}}</span>
				</div>
				<Field
					class="mt-3"
					:label="needsRemarks ? 'Reason for short / excess' : 'Remarks'"
					:required="needsRemarks"
					:hint="needsRemarks ? `Required: difference is above ₹${tolerance}` : ''"
				>
					<textarea v-model="doc.remarks" class="inp h-20 py-2" :disabled="!editable" />
				</Field>
			</Section>
		</div>

		<!-- STEP 5: review -->
		<div v-show="step === 4" class="grid grid-cols-1 gap-4 lg:grid-cols-3">
			<Section
				title="Summary"
				:class="
					full?.linked?.length || full?.events?.length
						? 'lg:col-span-2'
						: 'lg:col-span-3'
				"
			>
				<div
					v-if="checks.length"
					class="mb-4 space-y-1 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2"
				>
					<div class="text-[13px] font-semibold text-amber-800">
						Fix before submitting
					</div>
					<div
						v-for="c in checks"
						:key="c"
						class="flex items-start gap-2 text-[13px] text-amber-800"
					>
						<i class="lucide-circle-alert mt-0.5 size-4 shrink-0" />{{ c }}
					</div>
				</div>
				<div
					v-else-if="editable"
					class="mb-4 flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-[13px] text-green-800"
				>
					<i class="lucide-circle-check size-4" />Ready to submit.
				</div>
				<div class="grid grid-cols-2 gap-3 md:grid-cols-4">
					<AutoField label="Total sale (L)" :value="num(t.total_sale_qty)" />
					<AutoField label="Test (L)" :value="num(t.total_test_qty)" />
					<AutoField label="Gross sales" :value="inr(t.gross_sales)" />
					<AutoField label="Credit" :value="inr(t.credit_sales_amount)" />
					<AutoField label="Digital" :value="inr(t.digital_amount)" />
					<AutoField label="Expected cash" :value="inr(t.expected_cash)" />
					<AutoField label="Counted" :value="inr(t.cash_counted)" />
					<AutoField
						label="Short / excess"
						:value="signedInr(t.short_excess)"
						:tone="t.short_excess < -0.5 ? 'bad' : ''"
					/>
				</div>
				<div
					v-if="attRows.length"
					class="mt-4 overflow-x-auto rounded-lg border border-line"
				>
					<table class="tbl">
						<thead>
							<tr>
								<th>Attendant</th>
								<th>Nozzles</th>
								<th class="!text-right">Sale value</th>
								<th class="!text-right">Credit</th>
								<th class="!text-right">Digital</th>
								<th class="!text-right">Cash due</th>
								<th class="!text-right">Handed</th>
								<th class="!text-right">Short/Excess</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="a in attRows" :key="a.attendant">
								<td class="font-medium">{{ empName(a.attendant) }}</td>
								<td class="text-[12px]">{{ a.nozzles }}</td>
								<td class="r">{{ inr(a.sale_amount) }}</td>
								<td class="r">{{ inr(a.credit_amount) }}</td>
								<td class="r">{{ inr(a.digital_amount) }}</td>
								<td class="r">{{ inr(a.expected_cash) }}</td>
								<td class="r">{{ a.cash_handed ? inr(a.cash_handed) : "—" }}</td>
								<td
									class="r font-semibold"
									:class="
										a.short_excess < -0.5 ? 'text-red-600' : 'text-green-700'
									"
								>
									{{ a.cash_handed ? signedInr(a.short_excess) : "—" }}
								</td>
							</tr>
						</tbody>
					</table>
				</div>
				<div
					v-if="machineRows.length"
					class="mt-4 overflow-x-auto rounded-lg border border-line"
				>
					<table class="tbl">
						<thead>
							<tr>
								<th>Machine</th>
								<th>Side</th>
								<th>Nozzles</th>
								<th>Attendants</th>
								<th class="!text-right">Sale (L)</th>
								<th class="!text-right">Sale value</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="m in machineRows" :key="m.dispensing_unit + m.side">
								<td class="font-medium">{{ m.dispensing_unit }}</td>
								<td>{{ m.side }}</td>
								<td class="text-[12px]">{{ m.nozzles }}</td>
								<td class="text-[12px]">{{ m.attendants }}</td>
								<td class="r">{{ num(m.sale_qty) }}</td>
								<td class="r">{{ inr(m.sale_amount) }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</Section>
			<div class="space-y-4">
				<Section v-if="full?.events?.length" title="Approval trail" flush>
					<div class="divide-y divide-line">
						<div v-for="(e, i) in full.events" :key="i" class="px-4 py-2 text-[12px]">
							<b>{{ e.to === 1 ? "Submitted" : e.to === 2 ? "Cancelled" : e.to }}</b>
							· {{ e.by }} · <span class="text-ink-3">{{ dateTimeFmt(e.at) }}</span>
						</div>
					</div>
				</Section>
				<Section v-if="full?.linked?.length" title="Posted to ERPNext" flush>
					<div class="divide-y divide-line">
						<a
							v-for="l in full.linked"
							:key="l.name"
							:href="deskUrl(l.doctype, l.name)"
							target="_blank"
							class="flex items-center justify-between px-4 py-2 text-[12px] hover:bg-gray-50"
						>
							<span
								><b>{{ l.doctype }}</b
								><br /><span class="text-ink-3"
									>{{ l.name }} {{ l.customer ? "· " + l.customer : "" }}</span
								></span
							>
							<span class="num">{{ l.grand_total ? inr(l.grand_total) : "" }}</span>
						</a>
					</div>
				</Section>
			</div>
		</div>

		<!-- Mobile step nav -->
		<div class="mt-6 flex justify-between gap-2">
			<button class="btn-secondary" :disabled="step === 0" @click="step--">
				<i class="lucide-chevron-left size-4" />Back
			</button>
			<button v-if="step < steps.length - 1" class="btn-primary" @click="step++">
				Next<i class="lucide-chevron-right size-4" />
			</button>
		</div>

		<Modal v-model="rejectOpen" title="Reject shift closing">
			<Field label="Reason" required>
				<textarea v-model="rejectReason" class="inp h-24 py-2" />
			</Field>
			<template #footer>
				<button class="btn-secondary" @click="rejectOpen = false">Close</button>
				<button
					class="btn-danger"
					:disabled="!rejectReason || busy"
					@click="doTransition('Reject', rejectReason)"
				>
					Reject
				</button>
			</template>
		</Modal>
	</div>
	<div v-else class="space-y-3">
		<Skeleton class="h-10 w-64" /><Skeleton class="h-40 w-full" /><Skeleton
			class="h-64 w-full"
		/>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, h, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { toast } from "frappe-ui";
import { api, errorText, getList, printUrl, deskUrl } from "../api";
import { session } from "../session";
import {
	inr,
	num,
	litres,
	signedInr,
	dateFmt,
	timeFmt,
	dateTimeFmt,
	flt,
	today,
	addDays,
} from "../format";
import PageHeader from "../components/PageHeader.vue";
import Section from "../components/Section.vue";
import Field from "../components/Field.vue";
import AutoField from "../components/AutoField.vue";
import NumInput from "../components/NumInput.vue";
import LinkInput from "../components/LinkInput.vue";
import FuelChip from "../components/FuelChip.vue";
import EmployeeSelect from "../components/EmployeeSelect.vue";
import StatusPill from "../components/StatusPill.vue";
import EmptyState from "../components/EmptyState.vue";
import Modal from "../components/Modal.vue";
import Skeleton from "../components/Skeleton.vue";

const Row = (p) =>
	h(
		"div",
		{
			class: [
				"flex justify-between",
				p.bold ? "border-t border-line pt-1.5 font-semibold" : "text-ink-2",
			],
		},
		[h("dt", p.label), h("dd", { class: "num" }, inr(p.v))]
	);
Row.props = ["label", "v", "bold"];

const props = defineProps({ name: String });
const route = useRoute();
const router = useRouter();
const doc = ref(null);
const full = ref(null);
const step = ref(0);
const busy = ref(false);
const previewing = ref(false);
const serverError = ref("");
const modes = ref([]);
const limits = ref({});
const fuelSummary = ref([]);
const rejectOpen = ref(false);
const rejectReason = ref("");
const tabEls = [];
watch(step, (i) => {
	const el = tabEls[i];
	if (el) el.parentElement.scrollLeft = el.offsetLeft - el.parentElement.offsetLeft - 24;
	const top = el?.parentElement?.getBoundingClientRect().top;
	if (top !== undefined && top < 0) window.scrollBy({ top: top - 120 });
});
let key = 0;
let timer;

const isNew = computed(() => !props.name);
const shiftHours = computed(() => {
	const s = (session.boot.shifts || []).find((x) => x.name === doc.value?.shift);
	return s ? `${timeFmt(s.start_time)} – ${timeFmt(s.end_time)}` : "";
});
const machines = computed(() => session.boot.machines || []);
const machineRows = computed(() => doc.value?.machine_summary || []);
const attRows = computed(() => doc.value?.attendant_collection || []);
const shiftPeople = computed(() => [
	...new Set((doc.value?.nozzle_readings || []).map((r) => r.attendant).filter(Boolean)),
]);
const initials = (n) =>
	String(n || "?")
		.split(" ")
		.map((x) => x[0])
		.slice(0, 2)
		.join("")
		.toUpperCase();
const nozzleSide = {};
function sideAttendant(g, side) {
	const rows = g.rows.filter((r) => (nozzleSide[r.nozzle] || "") === side);
	const set = [...new Set(rows.map((r) => r.attendant).filter(Boolean))];
	return set.length === 1 ? set[0] : "";
}
function setSide(g, side, emp) {
	g.rows
		.filter((r) => (nozzleSide[r.nozzle] || "") === side)
		.forEach((r) => (r.attendant = emp));
	recalc();
}
const digitalByMode = computed(() => {
	const m = {};
	(doc.value?.payments || []).forEach((p) => {
		if (p.amount) m[p.mode_of_payment] = (m[p.mode_of_payment] || 0) + flt(p.amount);
	});
	return Object.entries(m).map(([mode, amount]) => ({ mode, amount }));
});
const empNames = ref({});
const nozzleDu = {};
const empName = (e) => empNames.value[e] || e || "—";

// same rule as the server: a tolerance of 0 (or unset) means no reason is ever required
const tolerance = computed(() => flt(session.boot.settings?.cash_variance_tolerance));
const editable = computed(
	() =>
		isNew.value ||
		(doc.value?.docstatus === 0 &&
			full.value?.can_write &&
			["Draft", "", null, undefined].includes(doc.value.workflow_state))
);
const stateLabel = computed(() =>
	isNew.value
		? "Draft"
		: doc.value.docstatus === 2
		? "Cancelled"
		: doc.value.workflow_state || (doc.value.docstatus ? "Submitted" : "Draft")
);
const transitions = computed(() => full.value?.transitions || []);
const submitAction = computed(() => {
	if (isNew.value)
		return session.boot.settings?.require_shift_approval
			? "Submit for Approval"
			: session.boot.can["Shift Sale Entry"].submit
			? "submit"
			: null;
	if (transitions.value.includes("Submit for Approval")) return "Submit for Approval";
	// no workflow (or one switched off after this draft was made, leaving workflow_state = "Draft"):
	// a plain submit is possible when the user may submit and no workflow action is on offer
	if (
		doc.value.docstatus === 0 &&
		full.value?.can_submit &&
		!transitions.value.length &&
		["Draft", "", null, undefined].includes(doc.value.workflow_state)
	)
		return "submit";
	return null;
});
const otherTransitions = computed(() =>
	transitions.value.filter((x) => x !== "Submit for Approval")
);
const t = computed(() => doc.value || {});
const needsRemarks = computed(
	() => tolerance.value > 0 && Math.abs(t.value.short_excess || 0) > tolerance.value
);
const steps = computed(() => [
	{ key: "meter", label: "Meter readings", count: doc.value?.nozzle_readings.length },
	{
		key: "sales",
		label: "Credit & other sales",
		count: (doc.value?.credit_sales.length || 0) + (doc.value?.other_sales.length || 0),
	},
	{ key: "coll", label: "Attendant collections" },
	{ key: "cash", label: "Cash count" },
	{ key: "review", label: "Review" },
]);
const groups = computed(() => {
	const g = {};
	for (const r of doc.value.nozzle_readings) {
		const du = (r.nozzle || "").split("-")[0] || "Nozzles";
		(g[du] = g[du] || []).push(r);
	}
	return Object.entries(g).map(([du, rows]) => ({
		du: du.startsWith("DU") ? `Machine ${du}` : du,
		rows,
		sides: [...new Set(rows.map((r) => nozzleSide[r.nozzle] || ""))].sort(),
	}));
});
const cashTone = computed(() => {
	const se = t.value.short_excess || 0;
	if (!t.value.cash_counted && !t.value.total_sale_qty)
		return {
			label: "Not counted yet",
			cls: "border-slate-200 bg-slate-50 text-ink-2",
			dot: "bg-slate-400",
			box: "bg-slate-50 text-ink-2",
		};
	if (Math.abs(se) < 1)
		return {
			label: "Cash tallied",
			cls: "border-green-200 bg-green-50 text-green-700",
			dot: "bg-green-600",
			box: "bg-green-50 text-green-800",
		};
	if (se < 0)
		return {
			label: `Short ${inr(-se)}`,
			cls: "border-red-200 bg-red-50 text-red-700",
			dot: "bg-red-600",
			box: "bg-red-50 text-red-700",
		};
	return {
		label: `Excess ${inr(se)}`,
		cls: "border-amber-200 bg-amber-50 text-amber-700",
		dot: "bg-amber-500",
		box: "bg-amber-50 text-amber-800",
	};
});
const checks = computed(() => {
	if (!editable.value) return [];
	const c = [];
	if (!doc.value.shift) c.push("Select the shift.");
	if (!doc.value.nozzle_readings.length) c.push("Load the nozzle readings.");
	if (doc.value.nozzle_readings.some((r) => r.closing_reading < r.opening_reading))
		c.push("A closing reading is below its opening.");
	if (
		doc.value.nozzle_readings.length &&
		doc.value.nozzle_readings.every((r) => r.closing_reading === r.opening_reading)
	)
		c.push("No closing readings entered yet.");
	if (doc.value.nozzle_readings.some((r) => !r.attendant && flt(r.sale_qty) > 0))
		c.push("Choose the attendant for every nozzle that sold fuel (Meter readings step).");
	if (!t.value.cash_counted) c.push("Count the cash.");
	if (needsRemarks.value && !doc.value.remarks)
		c.push("Enter the reason for the cash difference.");
	const partial = (table) =>
		(doc.value[table] || []).some((r) => !isBlankRow(table, r) && !isValidRow(table, r));
	if (partial("credit_sales")) c.push("Complete every credit slip (customer and quantity).");
	if (doc.value.credit_sales.some((r) => r._attCleared && !r.attendant))
		c.push(
			"Some credit slips were filled by someone no longer on a nozzle — pick who filled them."
		);
	if (partial("other_sales"))
		c.push("Complete every lube / shop sale (item, quantity and rate).");
	if (partial("driver_cash")) c.push("Complete every driver cash row (customer and amount).");
	if (partial("expenses")) c.push("Complete every expense (expense head and amount).");
	if (partial("employee_advances"))
		c.push("Complete every staff advance (employee and amount).");
	if (partial("payments")) c.push("Every digital payment needs a mode and a positive amount.");
	if (orphanPayments.value.length)
		c.push(
			"Some UPI / card payments belong to someone no longer on a nozzle — reassign or remove them (Attendant collections step)."
		);
	if (serverError.value) c.push(serverError.value);
	return c;
});

// ---- child-table row rules (required fields per table)
const ROW_RULES = {
	credit_sales: {
		keys: ["customer", "vehicle", "slip_no"],
		nums: ["qty"],
		valid: (r) => r.customer && flt(r.qty) > 0,
	},
	// qty defaults to 1 on a new row, so it does not count as "typed"
	other_sales: {
		keys: ["item_code"],
		nums: ["rate"],
		valid: (r) => r.item_code && flt(r.qty) > 0 && flt(r.rate) > 0,
	},
	driver_cash: {
		keys: ["customer", "vehicle"],
		nums: ["amount"],
		valid: (r) => r.customer && flt(r.amount) > 0,
	},
	expenses: {
		keys: ["expense_account", "description"],
		nums: ["amount"],
		valid: (r) => r.expense_account && flt(r.amount) > 0,
	},
	employee_advances: {
		keys: ["employee", "remarks"],
		nums: ["amount"],
		valid: (r) => r.employee && flt(r.amount) > 0,
	},
	// a payment row with no amount is just an untouched input
	payments: { keys: [], nums: ["amount"], valid: (r) => r.mode_of_payment && flt(r.amount) > 0 },
};
function isBlankRow(table, r) {
	const rule = ROW_RULES[table];
	if (!rule) return false;
	return !rule.keys.some((k) => r[k]) && !rule.nums.some((k) => flt(r[k]));
}
function isValidRow(table, r) {
	const rule = ROW_RULES[table];
	return !rule || !!rule.valid(r);
}
const orphanPayments = computed(() => {
	const ppl = shiftPeople.value;
	return (doc.value?.payments || []).filter(
		(p) => p.attendant && flt(p.amount) && !ppl.includes(p.attendant)
	);
});
function reassignPayment(p, who) {
	if (!who) return;
	const target = who === "__counter" ? "" : who;
	const existing = doc.value.payments.find(
		(x) => x !== p && x.mode_of_payment === p.mode_of_payment && (x.attendant || "") === target
	);
	if (existing) {
		existing.amount = flt(flt(existing.amount) + flt(p.amount));
		if (!existing.reference_no && p.reference_no) existing.reference_no = p.reference_no;
		doc.value.payments.splice(doc.value.payments.indexOf(p), 1);
	} else {
		p.attendant = target || null;
	}
	recalc();
}
// most common diesel-like fuel on the nozzles, else the first nozzle's fuel, else the first fuel
function defaultFuel() {
	const rows = doc.value?.nozzle_readings || [];
	const diesel = /hsd|diesel/i;
	const count = {};
	rows.forEach((r) => {
		if (r.fuel_item && diesel.test(r.fuel_item))
			count[r.fuel_item] = (count[r.fuel_item] || 0) + 1;
	});
	const best = Object.entries(count).sort((a, b) => b[1] - a[1])[0];
	if (best) return best[0];
	if (rows[0]?.fuel_item) return rows[0].fuel_item;
	const fuels = session.boot.fuels || [];
	return (
		fuels.find((f) => diesel.test(f.name) || diesel.test(f.item_name || ""))?.name ||
		fuels[0]?.name ||
		""
	);
}
// when an attendant leaves the nozzles, his credit slips lose their "filled by"
watch(
	() => [doc.value, shiftPeople.value.join("|")],
	([d, people], [od, oldPeople]) => {
		if (!d || d !== od || people === oldPeople || !editable.value) return;
		const ppl = shiftPeople.value;
		d.credit_sales.forEach((r) => {
			if (r.attendant && !ppl.includes(r.attendant)) {
				r.attendant = "";
				r._attCleared = true;
			}
		});
		recalc();
	}
);

// a night shift (22:00-06:00) closed after midnight belongs to the previous business day
function businessDate(shiftName) {
	const s = (session.boot.shifts || []).find((x) => x.name === shiftName);
	if (!s) return today();
	const st = timeFmt(s.start_time),
		en = timeFmt(s.end_time),
		now = new Date().toTimeString().slice(0, 5);
	return st > en && now < en ? addDays(today(), -1) : today();
}
function blank() {
	const sh = route.query.shift || currentShift();
	return {
		doctype: "Shift Sale Entry",
		station: session.station,
		posting_date: route.query.date || businessDate(sh),
		shift: sh || "",
		cashier: session.boot.employee?.name || "",
		cashier_name: session.boot.employee?.employee_name || "",
		nozzle_readings: [],
		credit_sales: [],
		other_sales: [],
		driver_cash: [],
		payments: [],
		expenses: [],
		employee_advances: [],
		machine_summary: [],
		attendant_collection: [],
		opening_float: 0,
		cash_to_next_shift: 0,
		cash_to_safe: 0,
		denominations: [500, 200, 100, 50, 20, 10, 5, 2, 1].map((d) => ({
			denomination: d,
			count: 0,
			amount: 0,
			_key: ++key,
		})),
		remarks: "",
		docstatus: 0,
	};
}
function currentShift() {
	const now = new Date().toTimeString().slice(0, 5);
	const s = (session.boot.shifts || []).find((x) => {
		const st = timeFmt(x.start_time),
			en = timeFmt(x.end_time);
		return (st <= en && now >= st && now < en) || (st > en && (now >= st || now < en));
	});
	return s?.name;
}
function withKeys(d) {
	for (const f of [
		"nozzle_readings",
		"credit_sales",
		"other_sales",
		"driver_cash",
		"payments",
		"expenses",
		"employee_advances",
		"denominations",
		"machine_summary",
		"attendant_collection",
	]) {
		d[f] = (d[f] || []).map((r) => ({ ...r, _key: ++key }));
	}
	const seen = {};
	d.nozzle_readings.forEach((r) => {
		if (seen[r.nozzle]) r._priceRow = true;
		seen[r.nozzle] = true;
	});
	return d;
}

async function load() {
	try {
		await loadInner();
	} catch (e) {
		toast.error(errorText(e));
		if (props.name) router.replace("/shifts");
	}
}
async function loadInner() {
	modes.value = session.boot.payment_modes || [];
	const [nz, emps] = await Promise.all([
		getList("Fuel Nozzle Master", {
			filters: { station: session.station },
			fields: ["name", "dispensing_unit", "side"],
			limit_page_length: 200,
		}),
		getList("Employee", {
			filters: { company: session.boot.station?.company },
			fields: ["name", "employee_name"],
			limit_page_length: 500,
		}),
	]);
	nz.forEach((n) => {
		nozzleDu[n.name] = n.dispensing_unit;
		nozzleSide[n.name] = n.side || "";
	});
	empNames.value = Object.fromEntries(emps.map((e) => [e.name, e.employee_name]));
	if (props.name) {
		full.value = await api("get_doc_full", { doctype: "Shift Sale Entry", name: props.name });
		doc.value = withKeys(full.value.doc);
		fuelSummary.value = doc.value.fuel_summary || [];
	} else {
		full.value = null;
		doc.value = blank();
	}
	loadLimits();
	recalc(false);
	// a new closing starts with the outlet's active nozzles and their opening readings
	if (isNew.value && doc.value.station && !doc.value.nozzle_readings.length) {
		try {
			await loadNozzles();
		} catch (e) {
			toast.error(errorText(e));
		}
	}
}

async function loadLimits() {
	try {
		const rows = await api("credit_customers");
		limits.value = Object.fromEntries(rows.map((r) => [r.name, r]));
	} catch (e) {
		/* no permission */
	}
}
function limitOf(c) {
	const l = limits.value[c];
	if (!l || !l.limit) return null;
	const thisShift =
		doc.value.credit_sales
			.filter((r) => r.customer === c)
			.reduce((a, r) => a + flt(r.amount), 0) +
		(doc.value.docstatus
			? 0
			: doc.value.driver_cash
					.filter((r) => r.customer === c)
					.reduce((a, r) => a + flt(r.amount), 0));
	const used = l.outstanding + (doc.value.docstatus ? 0 : thisShift);
	const pct = (used * 100) / l.limit;
	return {
		pct,
		over: used > l.limit,
		text: `${inr(used, true)} of ${inr(l.limit, true)} used${
			used > l.limit ? " — limit exceeded" : ""
		}`,
	};
}

async function loadNozzles() {
	if (
		doc.value.nozzle_readings.some((r) => r.closing_reading !== r.opening_reading) &&
		!window.confirm("Replace the entered readings with fresh nozzle data?")
	)
		return;
	let rows;
	try {
		rows = await api(
			"petrodiesel.petrodiesel.doctype.shift_sale_entry.shift_sale_entry.get_nozzles",
			{ station: doc.value.station, posting_date: doc.value.posting_date }
		);
	} catch (e) {
		toast.error(errorText(e));
		return;
	}
	doc.value.nozzle_readings = rows.map((r) => ({
		...r,
		test_qty: 0,
		attendant: "",
		_key: ++key,
	}));
	recalc();
}
function addPriceRow(r) {
	const idx = doc.value.nozzle_readings.indexOf(r);
	const opening = Math.max(
		...doc.value.nozzle_readings
			.filter((x) => x.nozzle === r.nozzle)
			.map((x) => flt(x.closing_reading))
	);
	doc.value.nozzle_readings.splice(idx + 1, 0, {
		nozzle: r.nozzle,
		fuel_item: r.fuel_item,
		tank: r.tank,
		attendant: r.attendant,
		opening_reading: opening,
		closing_reading: opening,
		test_qty: 0,
		rate: r.rate,
		_priceRow: true,
		_key: ++key,
	});
	recalc();
}
function addRow(table, vals) {
	const row = { ...vals, _key: ++key };
	if (table === "credit_sales") row.rate = rateFor(row.fuel_item);
	doc.value[table].push(row);
}
function removeRow(table, r) {
	doc.value[table].splice(doc.value[table].indexOf(r), 1);
	recalc();
}
function rateFor(item) {
	// boot fuel rates are today's price; for another date leave 0 and let the server fill it
	const bootRate =
		doc.value.posting_date === session.boot.today
			? (session.boot.fuels || []).find((f) => f.name === item)?.rate
			: 0;
	return doc.value.nozzle_readings.find((n) => n.fuel_item === item)?.rate || bootRate || 0;
}
function setCreditRate(r) {
	r.rate = rateFor(r.fuel_item);
	recalc();
}
async function onVehicle(r) {
	if (!r.vehicle) return;
	const v = (
		await getList("Customer Vehicle", {
			filters: { name: r.vehicle },
			fields: ["customer", "fuel_item", "driver_name"],
		})
	)[0];
	if (!v) return;
	if (!r.customer) r.customer = v.customer;
	if (v.fuel_item) r.fuel_item = v.fuel_item;
	if (v.driver_name) r.driver_name = v.driver_name;
	setCreditRate(r);
}
async function onItem(r) {
	if (!r.item_code) return;
	r.rate = await api("petrodiesel.petrodiesel.utils.get_rate", {
		item_code: r.item_code,
		posting_date: doc.value.posting_date,
	});
	recalc();
}
function payment(mode, who = "") {
	return (
		doc.value.payments.find(
			(p) => p.mode_of_payment === mode && (p.attendant || "") === who
		) || { amount: 0, reference_no: "" }
	);
}
function setPayment(mode, who, field, val) {
	let p = doc.value.payments.find(
		(x) => x.mode_of_payment === mode && (x.attendant || "") === who
	);
	if (!p) {
		p = {
			mode_of_payment: mode,
			attendant: who || null,
			amount: 0,
			reference_no: "",
			_key: ++key,
		};
		doc.value.payments.push(p);
	}
	p[field] = val;
	recalc();
}
function modeIcon(m) {
	const k = m.toLowerCase();
	if (k.includes("upi")) return "lucide-qr-code";
	if (k.includes("card") && !k.includes("fleet")) return "lucide-credit-card";
	if (k.includes("fleet")) return "lucide-truck";
	return "lucide-landmark";
}
function onHeader() {
	if (!editable.value) return;
	// rates belong to the business date: drop them so the server price list refills them
	// (manual price-change rows keep what the user typed)
	doc.value.nozzle_readings.forEach((r) => {
		if (!r._priceRow) r.rate = 0;
	});
	doc.value.credit_sales.forEach((r) => (r.rate = 0));
	// nothing typed yet: reload nozzles so openings and rates match the new date
	if (
		isNew.value &&
		!doc.value.nozzle_readings.some((r) => r.closing_reading !== r.opening_reading)
	) {
		loadNozzles().catch((e) => toast.error(errorText(e)));
		return;
	}
	recalc();
}

// ---- live maths: same rules as the server; server preview confirms
function recalc(sync = true) {
	const d = doc.value;
	d.nozzle_readings.forEach((r) => {
		r.meter_qty = flt(flt(r.closing_reading) - flt(r.opening_reading));
		r.sale_qty = flt(r.meter_qty - flt(r.test_qty));
		r.amount = flt(r.sale_qty * flt(r.rate));
	});
	d.credit_sales.forEach((r) => {
		if (!r.rate) r.rate = rateFor(r.fuel_item);
		r.amount = flt(flt(r.qty) * flt(r.rate));
	});
	d.other_sales.forEach((r) => (r.amount = flt(flt(r.qty) * flt(r.rate))));
	d.denominations.forEach((r) => (r.amount = flt((r.denomination || 0) * (r.count || 0))));
	const sum = (a, f) => a.reduce((x, r) => x + flt(r[f]), 0);
	let creditAtMeter = 0;
	d.credit_sales.forEach((c) => {
		creditAtMeter += flt(c.qty) * flt(rateFor(c.fuel_item) || c.rate);
	});
	const retailFuel = sum(d.nozzle_readings, "amount") - creditAtMeter;
	d.total_meter_qty = flt(sum(d.nozzle_readings, "meter_qty"));
	d.total_test_qty = flt(sum(d.nozzle_readings, "test_qty"));
	d.total_sale_qty = flt(sum(d.nozzle_readings, "sale_qty"));
	d.credit_sales_amount = flt(sum(d.credit_sales, "amount"));
	d.fuel_sales_amount = flt(retailFuel + d.credit_sales_amount);
	d.other_sales_amount = flt(sum(d.other_sales, "amount"));
	d.gross_sales = flt(d.fuel_sales_amount + d.other_sales_amount);
	d.digital_amount = flt(sum(d.payments, "amount"));
	d.expense_amount = flt(sum(d.expenses, "amount"));
	d.advance_amount = flt(sum(d.employee_advances, "amount"));
	d.driver_cash_amount = flt(sum(d.driver_cash, "amount"));
	d.expected_cash = flt(
		retailFuel +
			d.other_sales_amount -
			d.digital_amount -
			d.expense_amount -
			d.advance_amount -
			d.driver_cash_amount +
			flt(d.opening_float)
	);
	d.cash_counted = flt(sum(d.denominations, "amount"));
	d.short_excess = flt(d.cash_counted - d.expected_cash);
	d.cash_to_safe = flt(d.cash_counted - flt(d.cash_to_next_shift));
	// machine sides (sales only) and attendant collections — same rules as the server
	const sides = {};
	d.nozzle_readings.forEach((r) => {
		const du = nozzleDu[r.nozzle];
		if (!du) return;
		const k = du + "|" + (nozzleSide[r.nozzle] || "");
		const m = (sides[k] = sides[k] || {
			dispensing_unit: du,
			side: nozzleSide[r.nozzle] || "",
			nozzles: [],
			attendants: [],
			sale_qty: 0,
			sale_amount: 0,
		});
		if (!m.nozzles.includes(r.nozzle)) m.nozzles.push(r.nozzle);
		if (r.attendant && !m.attendants.includes(empName(r.attendant)))
			m.attendants.push(empName(r.attendant));
		m.sale_qty += flt(r.sale_qty);
		m.sale_amount += flt(r.amount);
	});
	d.machine_summary = Object.values(sides).map((m) => ({
		...m,
		nozzles: m.nozzles.join(", "),
		attendants: m.attendants.join(", "),
		sale_qty: flt(m.sale_qty),
		sale_amount: flt(m.sale_amount),
	}));
	const handed = Object.fromEntries(
		(d.attendant_collection || []).map((a) => [a.attendant, flt(a.cash_handed)])
	);
	const ppl = {};
	d.nozzle_readings.forEach((r) => {
		if (!r.attendant) return;
		const p = (ppl[r.attendant] = ppl[r.attendant] || {
			attendant: r.attendant,
			nozzles: [],
			sale_qty: 0,
			sale_amount: 0,
			credit_amount: 0,
			digital_amount: 0,
		});
		if (!p.nozzles.includes(r.nozzle)) p.nozzles.push(r.nozzle);
		p.sale_qty += flt(r.sale_qty);
		p.sale_amount += flt(r.amount);
	});
	d.credit_sales.forEach((c) => {
		if (ppl[c.attendant]) ppl[c.attendant].credit_amount += flt(c.amount);
	});
	d.payments.forEach((p) => {
		if (ppl[p.attendant]) ppl[p.attendant].digital_amount += flt(p.amount);
	});
	d.attendant_collection = Object.values(ppl).map((p) => {
		const due = flt(p.sale_amount - p.credit_amount - p.digital_amount);
		const cash = handed[p.attendant] || 0;
		return {
			...p,
			nozzles: p.nozzles.join(", "),
			sale_qty: flt(p.sale_qty),
			sale_amount: flt(p.sale_amount),
			credit_amount: flt(p.credit_amount),
			digital_amount: flt(p.digital_amount),
			expected_cash: due,
			cash_handed: cash,
			short_excess: cash ? flt(cash - due) : 0,
		};
	});
	if (sync !== false && editable.value) schedule();
}
function schedule() {
	clearTimeout(timer);
	timer = setTimeout(preview, 700);
}
function payload(forPreview = false) {
	const d = JSON.parse(JSON.stringify(doc.value));
	// rows nobody typed into would fail the server's required fields: drop them
	for (const f of Object.keys(ROW_RULES)) d[f] = (d[f] || []).filter((r) => !isBlankRow(f, r));
	if (forPreview) {
		d.credit_sales = d.credit_sales.filter((r) => r.customer && flt(r.qty) > 0);
		d.other_sales = d.other_sales.filter((r) => r.item_code && flt(r.qty) > 0);
		d.driver_cash = d.driver_cash.filter((r) => r.customer && flt(r.amount) > 0);
		d.expenses = d.expenses.filter((r) => r.expense_account && flt(r.amount) > 0);
		d.employee_advances = d.employee_advances.filter((r) => r.employee && flt(r.amount) > 0);
	}
	if (isNew.value) delete d.name;
	for (const f of [
		"nozzle_readings",
		"credit_sales",
		"other_sales",
		"driver_cash",
		"payments",
		"expenses",
		"employee_advances",
		"denominations",
		"machine_summary",
		"attendant_collection",
	]) {
		d[f] = (d[f] || [])
			.filter((r) => f !== "payments" || flt(r.amount))
			.map((r) => Object.fromEntries(Object.entries(r).filter(([k]) => !k.startsWith("_"))));
	}
	delete d.fuel_summary;
	return d;
}
async function preview() {
	if (!doc.value.shift || !doc.value.nozzle_readings.length) return;
	previewing.value = true;
	try {
		const r = await api("preview", { doc: payload(true) });
		serverError.value = r.error || "";
		fuelSummary.value = r.doc.fuel_summary || [];
		// adopt authoritative totals from the server
		for (const f of [
			"fuel_sales_amount",
			"gross_sales",
			"credit_sales_amount",
			"expected_cash",
			"short_excess",
			"total_sale_qty",
			"opening_float",
			"previous_entry",
			"cash_to_safe",
		]) {
			if (r.doc[f] !== undefined && r.doc[f] !== null) doc.value[f] = r.doc[f];
		}
		let filled = false;
		r.doc.nozzle_readings?.forEach((sr, i) => {
			const lr = doc.value.nozzle_readings[i];
			if (lr && !flt(lr.rate) && flt(sr.rate)) {
				lr.rate = sr.rate;
				filled = true;
			}
		});
		// credit rows are filtered in the preview payload, so match them by fuel
		const serverCreditRate = {};
		(r.doc.credit_sales || []).forEach((sr) => {
			if (flt(sr.rate)) serverCreditRate[sr.fuel_item] = sr.rate;
		});
		doc.value.credit_sales.forEach((cr) => {
			if (flt(cr.rate)) return;
			const rate = rateFor(cr.fuel_item) || serverCreditRate[cr.fuel_item];
			if (rate) {
				cr.rate = rate;
				filled = true;
			}
		});
		if (filled) recalc(false);
	} catch (e) {
		serverError.value = errorText(e);
	} finally {
		previewing.value = false;
	}
}

async function save(action) {
	if (busy.value) return;
	if (action && checks.value.length) {
		step.value = 4;
		toast.error(
			checks.value[0] +
				(checks.value.length > 1 ? ` (+${checks.value.length - 1} more)` : "")
		);
		return;
	}
	busy.value = true;
	try {
		const name = await api("save_doc", { doc: payload(), action: action || null });
		toast.success(
			action
				? action === "submit"
					? "Shift posted to ERPNext"
					: "Sent for approval"
				: "Draft saved"
		);
		if (isNew.value) router.replace(`/shifts/${name}`);
		else await load();
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
}
function transition(tn) {
	if (busy.value) return;
	if (tn === "Reject") {
		rejectReason.value = "";
		rejectOpen.value = true;
		return;
	}
	if (
		tn === "Cancel" &&
		!window.confirm(
			"Cancel this shift? Its invoices and journal will be cancelled too. Later shifts on the same nozzles must be cancelled first."
		)
	)
		return;
	doTransition(tn);
}
async function doTransition(tn, reason) {
	if (busy.value) return;
	busy.value = true;
	try {
		await api("doc_action", {
			doctype: "Shift Sale Entry",
			name: doc.value.name,
			action: tn,
			reason,
		});
		toast.success(tn === "Approve" ? "Approved and posted to ERPNext" : `${tn} done`);
		rejectOpen.value = false;
		rejectReason.value = "";
		await load();
	} catch (e) {
		toast.error(errorText(e));
	} finally {
		busy.value = false;
	}
}

onMounted(load);
</script>
