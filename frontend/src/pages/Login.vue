<template>
	<div class="grid min-h-screen bg-canvas lg:grid-cols-2">
		<div
			class="relative hidden overflow-hidden bg-brand-700 p-12 text-white lg:flex lg:flex-col"
		>
			<div class="flex items-center gap-3">
				<img
					:src="'/assets/petrodiesel/images/logo.svg'"
					class="size-10 rounded-lg ring-2 ring-white/20"
					alt=""
				/>
				<span class="text-[20px] font-semibold">PetroDesk</span>
			</div>
			<div class="mt-auto max-w-md">
				<h1 class="text-[36px] font-bold leading-tight tracking-tight">
					Every litre, every rupee, reconciled.
				</h1>
				<p class="mt-4 text-[15px] text-brand-100">
					Shift closing, tanker decantation, dips, DSR and credit customers for your fuel
					outlet, posted straight to ERPNext.
				</p>
				<div class="mt-8 grid grid-cols-3 gap-3 text-[12px]">
					<div class="rounded-lg bg-white/10 p-3">
						<div class="text-[18px] font-semibold">MS</div>
						Petrol
					</div>
					<div class="rounded-lg bg-white/10 p-3">
						<div class="text-[18px] font-semibold">HSD</div>
						Diesel
					</div>
					<div class="rounded-lg bg-white/10 p-3">
						<div class="text-[18px] font-semibold">DSR</div>
						Daily stock
					</div>
				</div>
			</div>
			<svg class="absolute -right-24 -top-24 size-96 text-white/5" viewBox="0 0 100 100">
				<circle cx="50" cy="50" r="50" fill="currentColor" />
			</svg>
		</div>

		<div class="flex items-center justify-center p-6">
			<form class="w-full max-w-sm" @submit.prevent="submit">
				<div class="mb-8 flex items-center gap-3 lg:hidden">
					<img
						:src="'/assets/petrodiesel/images/logo.svg'"
						class="size-10 rounded-lg"
						alt=""
					/>
					<span class="text-[20px] font-semibold">PetroDesk</span>
				</div>
				<h2 class="text-[24px] font-semibold tracking-tight">Sign in</h2>
				<p class="mt-1 text-[14px] text-ink-2">Use your outlet account.</p>

				<div class="mt-6 space-y-4">
					<Field label="Email or mobile">
						<input
							v-model="usr"
							class="inp h-11"
							autocomplete="username"
							autofocus
							required
						/>
					</Field>
					<Field label="Password">
						<div class="relative">
							<input
								v-model="pwd"
								:type="show ? 'text' : 'password'"
								class="inp h-11 pr-10"
								autocomplete="current-password"
								required
							/>
							<button
								type="button"
								class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-ink-3"
								@click="show = !show"
							>
								<i
									:class="show ? 'lucide-eye-off' : 'lucide-eye'"
									class="size-4"
								/>
							</button>
						</div>
					</Field>
					<div
						v-if="error"
						class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-red-700"
					>
						{{ error }}
					</div>
					<button class="btn-primary h-11 w-full" :disabled="busy">
						<i v-if="busy" class="lucide-loader-circle size-4 animate-spin" />Sign in
					</button>
					<a
						href="/login#forgot"
						class="block text-center text-[13px] text-brand-600 hover:underline"
						>Forgot password?</a
					>
				</div>
				<p class="mt-10 text-center text-[11px] text-ink-3">
					PetroDesk · Powered by ERPNext
				</p>
			</form>
		</div>
	</div>
</template>
<script setup>
import { ref } from "vue";
import Field from "../components/Field.vue";
import { login } from "../session";
import { errorText } from "../api";

const usr = ref("");
const pwd = ref("");
const show = ref(false);
const busy = ref(false);
const error = ref("");
async function submit() {
	busy.value = true;
	error.value = "";
	try {
		await login(usr.value.trim(), pwd.value);
	} catch (e) {
		const t = errorText(e);
		error.value = /disabled/i.test(t)
			? "This account is disabled. Contact the outlet owner."
			: "Invalid login. Check email and password.";
	} finally {
		busy.value = false;
	}
}
</script>
