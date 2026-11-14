<template>
	<AppShell v-if="session.loggedIn && route.name !== 'Login'">
		<RouterView :key="route.fullPath" />
	</AppShell>
	<RouterView v-else />
	<ToastProvider />
	<Dialogs />
</template>

<script setup>
import { useRoute } from "vue-router";
import { ToastProvider, Dialogs } from "frappe-ui";
import AppShell from "./components/AppShell.vue";
import { session } from "./session";

const route = useRoute();
</script>
