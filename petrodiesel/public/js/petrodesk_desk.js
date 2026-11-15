// PetroDesk: send desk sign-out and expired sessions to the PetroDesk sign-in page.
// The /login redirect hook does the same on the server; this keeps working even while
// Frappe still has the old /login page cached.
(function () {
	const target = () => {
		const back = window.location.pathname + window.location.search;
		return `/petrodiesel/login?redirect-to=${encodeURIComponent(back)}`;
	};
	const patch = (obj) => {
		if (obj && !obj.__petrodesk_login) {
			obj.redirect_to_login = function () {
				window.location.href = target();
			};
			obj.__petrodesk_login = true;
		}
	};
	if (window.frappe && frappe.Application) patch(frappe.Application.prototype);
	$(document).on("app_ready", () => patch(frappe.app));
})();
