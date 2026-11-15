import { reactive } from "vue";
import { call } from "frappe-ui";
import { api } from "./api";

export const session = reactive({
	ready: false,
	loggedIn: false,
	boot: null,
	station: null,
});

export async function loadBoot() {
	try {
		const b = await api("boot");
		session.boot = b;
		session.loggedIn = true;
		session.station = b.station?.name;
	} catch (e) {
		session.loggedIn = false;
		session.boot = null;
	} finally {
		session.ready = true;
	}
	return session.loggedIn;
}

export async function refreshCounts() {
	if (!session.loggedIn) return;
	try {
		session.boot.counts = await api("counts");
	} catch (e) {
		/* ignore */
	}
}

// Where to go after sign-in. `redirect` is an in-app path (set by the router guard);
// `redirect-to` is a site path (set by Frappe, e.g. /desk/...). Only same-site paths are honoured.
export function postLoginTarget(query = {}) {
	const safe = (p) => typeof p === "string" && p.startsWith("/") && !p.startsWith("//");
	const siteTarget = query["redirect-to"];
	if (safe(siteTarget) && !/^\/(login|petrodiesel\/login)\b/.test(siteTarget)) return siteTarget;
	if (safe(query.redirect) && query.redirect !== "/login")
		return "/petrodiesel" + query.redirect;
	return "/petrodiesel";
}

export async function login(usr, pwd, target = "/petrodiesel") {
	await call("login", { usr, pwd });
	// a new CSRF token is issued for the logged-in session; reload to pick it up
	window.location.href = target;
}

export async function resetPassword(user) {
	await call("frappe.core.doctype.user.user.reset_password", { user });
}

export async function logout() {
	await call("logout");
	window.location.href = "/petrodiesel/login";
}

export const hasRole = (...roles) =>
	!!session.boot && session.boot.roles.some((r) => roles.includes(r) || r === "System Manager");
export const can = (doctype, perm = "create") => !!session.boot?.can?.[doctype]?.[perm];
