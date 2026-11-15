import { call } from "frappe-ui";

export function api(method, args = {}) {
	const path = method.includes(".") ? method : `petrodiesel.api.${method}`;
	return call(path, args);
}

export function errorText(e) {
	if (!e) return "";
	const msgs = e.messages && e.messages.length ? e.messages : [e.message || String(e)];
	return msgs.map((m) => String(m).replace(/<[^>]+>/g, "")).join("\n");
}

export function searchLink(doctype, txt, filters) {
	return call("frappe.desk.search.search_link", {
		doctype,
		txt: txt || "",
		filters: filters || null,
		page_length: 20,
	}).then((r) => r || []);
}

export function getList(doctype, opts = {}) {
	return call("frappe.client.get_list", { doctype, limit_page_length: 100, ...opts });
}

export function deskUrl(doctype, name) {
	const slug = doctype.toLowerCase().replace(/ /g, "-");
	return name ? `/desk/${slug}/${encodeURIComponent(name)}` : `/desk/${slug}`;
}

export function printUrl(doctype, name, format) {
	const q = new URLSearchParams({ doctype, name, format: format || "", no_letterhead: 0 });
	return `/printview?${q.toString()}`;
}
