/* Desk-only tweaks for user menu and sidebar */
(() => {
  const onReady = (fn) => {
    if (window.frappe?.after_ajax) {
      frappe.after_ajax(fn);
    } else {
      $(document).ready(fn);
    }
  };

  const renderUserMenu = () => {
    const menu = $(".dropdown-menu.user-menu");
    if (!menu.length) return;

    menu.empty();

    const makeItem = (label, onClick) => {
      const li = $("<li class='user-action-item'></li>");
      const link = $("<a class='dropdown-item' role='menuitem' href='#'></a>").text(label);
      link.on("click", (e) => {
        e.preventDefault();
        onClick();
      });
      li.append(link);
      return li;
    };

    menu.append(
      makeItem(__('My Profile'), () => {
        if (frappe?.set_route) {
          frappe.set_route('Form', 'User', frappe.session.user);
        } else {
          window.location.href = '/app/user-profile';
        }
      })
    );

    menu.append(
      makeItem(__('Logout'), () => {
        if (frappe?.app?.logout) {
          frappe.app.logout();
        }
      })
    );
  };

  const removeSupportLinks = () => {
    const isSupportLabel = (el) => $(el).text().trim().toLowerCase() === 'support';
    $(".sidebar-item-label").filter((_, el) => isSupportLabel(el)).closest(".standard-sidebar-item, .sidebar-item-container, li").remove();
    $("[data-label='Support'], [data-name='Support']").remove();
  };

  const runOnce = () => {
    // Redirect old workspace routes containing '&' (%26) to clean slugs
    try {
      const route = window.location.pathname || "";
      if (route.startsWith("/app/")) {
        const slug = route.slice("/app/".length);
        const redirects = {
          "petrosoft---hr-%26-advances": "petrosoft---hr-advances",
          "petrosoft---tank-%26-stock": "petrosoft---tank-stock",
          "petrosoft---sales-%26-payments": "petrosoft---sales-payments",
        };
        if (redirects[slug] && frappe?.set_route) {
          frappe.set_route(redirects[slug]);
          return;
        }
      }
    } catch (e) {
      // ignore
    }
    renderUserMenu();
    removeSupportLinks();
  };

  onReady(() => {
    runOnce();
    $(document).on('toolbar_setup', renderUserMenu);
    frappe.router?.on('change', () => setTimeout(removeSupportLinks, 200));
  });
})();
