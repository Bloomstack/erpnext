// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Plant', {
	setup: function(frm) {
		frm.make_methods = {
			'Harvest': () => frappe.model.open_mapped_doc({
				method: "erpnext.agriculture.doctype.plant.plant.make_harvest",
				frm: frm
			})
		}
	}
});
