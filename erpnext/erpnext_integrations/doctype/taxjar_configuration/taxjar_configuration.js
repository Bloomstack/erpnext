// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('TaxJar Configuration', {
	refresh: (frm) => {
		frm.add_custom_button(__('Update Nexus List'), function() {
			frm.call({
				doc: frm.doc,
				method: 'update_nexus_list',
				callback: (r) => {
					if (r.message) {
						frappe.show_alert({
							indicator: 'green',
							message: __('Nexus List Updated')
						});
					}
				}
			});
		});
		frm.add_custom_button(__('Sync Product Tax Code'), function() {
			frm.call({
				doc: frm.doc,
				method: 'sync_product_tax_code',
				callback: (r) => {
					if (r.message) {
						frappe.show_alert({
							indicator: 'green',
							message: __('Categories List Updated')
						});
					}
				}
			});
		});
		frm.add_custom_button("Sign Up For Taxjar", function() {
			window.open('https://app.taxjar.com/api_sign_up');
		});
		frm.events.setup_progress(frm);
	},
	onload: (frm) => {
		frm.set_query('tax_account_head', (doc) => {
			return {
				filters: {
					"is_group": 0,
					"company": doc.company
				}
			};
		});
		frm.set_query('shipping_account_head', (doc) => {
			return {
				filters: {
					"is_group": 0,
					"company": doc.company
				}
			};
		});
	},
	setup_progress: function (frm) {
		frappe.realtime.on('creating_product_tax_code', (data) => {
			if (data.progress) {
				frm.dashboard.show_progress('Create Product Tax Code', data.progress / data.total * 100, data.label);
				if (data.progress === data.total) {
					frm.dashboard.hide_progress('Create Product Tax Code');
					frm.refresh();
				}
			}
		});
	},
	validate: (frm) => {
		if (frm.doc.enabled) {
			frm.call({
				doc: frm.doc,
				method: 'validate_api_key',
				callback: (r) => {
					if(r && !r.message.error) {
						frm.set_value("is_verified", 1);
						frappe.msgprint(__(`The API Key has been successfully Verified`));
					} else {
						frm.set_value("is_verified", 0);
						frappe.msgprint(__(`The API Key is Invalid. ${r.message.error}`));
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
