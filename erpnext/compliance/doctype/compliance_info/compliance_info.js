// Copyright (c) 2019, Bloom Stack, Inc and contributors
// For license information, please see license.txt

frappe.ui.form.on('Compliance Info', {
	setup: function (frm) {
		frm.make_methods = {
			'Customer': () => frappe.model.open_mapped_doc({
				method: 'erpnext.compliance.doctype.compliance_info.compliance_info.create_customer',
				frm: frm
			}),
			'Supplier': () => frappe.model.open_mapped_doc({
				method: 'erpnext.compliance.doctype.compliance_info.compliance_info.create_supplier',
				frm: frm
			})
		};
	}
});
