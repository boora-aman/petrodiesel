import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { toast } from "frappe-ui";
import { api, errorText } from "../api";
import { session } from "../session";

const WORKFLOW_DOCTYPES = ["Tanker Receipt", "Shift Sale Entry"];
const hasWorkflow = (dt) => WORKFLOW_DOCTYPES.includes(dt);

let key = 0;
export const nextKey = () => ++key;

export function useDocForm({ doctype, name, blank, tables = [], route, onLoaded }) {
	const router = useRouter();
	const doc = ref(null);
	const full = ref(null);
	const busy = ref(false);
	const serverError = ref("");
	const previewing = ref(false);
	let timer;

	const isNew = computed(() => !name);
	const editable = computed(
		() =>
			isNew.value ||
			(doc.value?.docstatus === 0 &&
				full.value?.can_write &&
				["Draft", "", null, undefined].includes(doc.value.workflow_state))
	);
	const transitions = computed(() => full.value?.transitions || []);
	const state = computed(() => {
		if (!doc.value) return "";
		if (isNew.value) return "Draft";
		if (doc.value.docstatus === 2) return "Cancelled";
		return doc.value.workflow_state || (doc.value.docstatus === 1 ? "Submitted" : "Draft");
	});
	const sendAction = computed(() => {
		if (!editable.value) return null;
		const wf = transitions.value.find((t) => /Submit for|Send for/.test(t));
		if (wf) return wf;
		if (isNew.value)
			return session.boot.can?.[doctype]?.submit || hasWorkflow(doctype) ? "auto" : null;
		// a draft left over from when approval was on: submit directly if no workflow applies now
		if (transitions.value.length) return null;
		return full.value?.can_submit ? "submit" : null;
	});

	function withKeys(d) {
		tables.forEach((t) => {
			d[t] = (d[t] || []).map((r) => ({ ...r, _key: nextKey() }));
		});
		return d;
	}
	function payload() {
		const d = JSON.parse(JSON.stringify(doc.value));
		if (isNew.value) delete d.name;
		tables.forEach((t) => {
			d[t] = (d[t] || []).map(({ _key, ...r }) => r);
		});
		return d;
	}
	async function load() {
		try {
			if (name) {
				full.value = await api("get_doc_full", { doctype, name });
				doc.value = withKeys(full.value.doc);
			} else {
				full.value = null;
				doc.value = withKeys(await blank());
			}
			onLoaded && onLoaded(doc.value);
		} catch (e) {
			toast.error(errorText(e));
			if (name) router.replace(route);
		}
	}
	async function preview(apply) {
		previewing.value = true;
		try {
			const r = await api("preview", { doc: payload() });
			serverError.value = r.error || "";
			apply && apply(r.doc);
			return r;
		} catch (e) {
			serverError.value = errorText(e);
		} finally {
			previewing.value = false;
		}
	}
	function schedule(apply, ms = 600) {
		clearTimeout(timer);
		timer = setTimeout(() => preview(apply), ms);
	}

	async function save(action) {
		if (busy.value) return;
		busy.value = true;
		let n = null;
		const goTo = async () => {
			if (isNew.value && n) router.replace(`${route}/${encodeURIComponent(n)}`);
			else await load();
		};
		try {
			let act = action;
			if (act === "auto") act = null;
			n = await api("save_doc", { doc: payload(), action: act });
			let msg = action ? "Submitted" : "Draft saved";
			if (action === "auto" && isNew.value) {
				// new document: after first save see if a workflow applies
				try {
					const f = await api("get_doc_full", { doctype, name: n });
					const wf = f.transitions.find((t) => /Submit for|Send for/.test(t));
					if (wf) {
						await api("doc_action", { doctype, name: n, action: wf });
						msg =
							wf === "Send for Verification"
								? "Sent for verification"
								: "Sent for approval";
					} else if (f.can_submit)
						await api("doc_action", { doctype, name: n, action: "submit" });
					else msg = "Saved as draft. A manager will submit it.";
				} catch (e) {
					// the draft is saved: open it so a retry does not create a second one
					toast.error(`Saved as draft ${n}, but not submitted: ${errorText(e)}`);
					await goTo();
					return n;
				}
			}
			toast.success(msg);
			await goTo();
			return n;
		} catch (e) {
			toast.error(errorText(e));
		} finally {
			busy.value = false;
		}
	}
	async function act(action, reason) {
		if (busy.value) return;
		if (action === "Cancel" || action === "cancel_doc") {
			if (
				!window.confirm(
					"Cancel this document? Linked ERPNext entries will be cancelled too."
				)
			)
				return;
		}
		busy.value = true;
		try {
			await api("doc_action", { doctype, name: doc.value.name, action, reason });
			toast.success(`${action === "cancel_doc" ? "Cancelled" : action} done`);
			await load();
		} catch (e) {
			toast.error(errorText(e));
		} finally {
			busy.value = false;
		}
	}
	return {
		doc,
		full,
		busy,
		serverError,
		previewing,
		isNew,
		editable,
		transitions,
		state,
		sendAction,
		load,
		save,
		act,
		preview,
		schedule,
		payload,
	};
}
