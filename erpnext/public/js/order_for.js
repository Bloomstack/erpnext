frappe.ready(function () {

    $('.order-for-contact-logout').click(function() {
        frappe.call("erpnext.utilities.order_for.reset_website_customer").then(r => {
          window.location.href = r.message;
        });
      });
});
