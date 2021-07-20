// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('TaxJar Settings', {
	is_sandbox: (frm) => {
		frm.toggle_reqd("api_key", !frm.doc.is_sandbox);
		frm.toggle_reqd("sandbox_api_key", frm.doc.is_sandbox);
	}
});
frappe.ui.form.on("TaxJar Settings", "refresh", function(frm) {
	frm.add_custom_button("Sign Up For Taxjar", function() {
		window.open('https://app.taxjar.com/api_sign_up');
	});
});