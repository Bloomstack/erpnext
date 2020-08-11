// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Plant', {
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Manicure / Harvest"), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.agriculture.doctype.plant.plant.make_harvest",
					frm: frm
				});
			}, __("Create"));
			frm.add_custom_button(__("Additive Log"), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.agriculture.doctype.plant.plant.make_additive_log",
					frm: frm
				});
			}, __("Create"));
			frm.add_custom_button(__("Disease Diagnosis"), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.agriculture.doctype.plant.plant.make_disease_diagnosis",
					frm: frm
				});
			}, __("Create"));
		}
	}
});
