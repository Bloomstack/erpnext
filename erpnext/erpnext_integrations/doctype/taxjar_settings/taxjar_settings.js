// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('TaxJar Settings', {
	refresh: (frm) => {
		frm.add_custom_button("Sign Up For Taxjar", function() {
			window.open('https://app.taxjar.com/api_sign_up');
		});
	},
	onload: (frm) => {
		frm.set_query('tax_account_head', (doc) => {
			return {
				filters: {
					"company": doc.company
				}
			};
		});
		frm.set_query('shipping_account_head', (doc) => {
			return {
				filters: {
					"company": doc.company
				}
			};
		});
	},
	validate: (frm) => {
		if (frm.doc.enabled) {
			frm.call({
				doc: frm.doc,
				method: 'validate_api_key',
				callback: (r) => {
					if(r && r.message){
						frappe.show_alert({
							indicator: 'green',
							message: __('TaxJar api key is Valid')
						})
					} else {
						frappe.show_alert({
							indicator: 'red',
							message: __('TaxJar api key is Invalid')
						})
					}
				},
			});
		}
	},
	is_sandbox: (frm) => {
		frm.toggle_reqd("api_key", !frm.doc.is_sandbox);
		frm.toggle_reqd("sandbox_api_key", frm.doc.is_sandbox);
	}
});