// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Settings', {
	refresh: (frm) => {
		frm.add_custom_button(__("Sync Data"), () => {
			frappe.call({
				method: "erpnext.compliance.utils.sync_data"
			});
		}).addClass("btn-primary");
	}
});
