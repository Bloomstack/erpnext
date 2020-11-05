// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier Group', {
	setup: function(frm) {
		frm.fields_dict['parent_supplier_group'].get_query = function(doc) {
			return {
				filters:[
					['Supplier Group', 'is_group', '=', 1],
					['Supplier Group', 'name', "!=", doc.supplier_group_name]
				]
			};
		};
		frm.fields_dict['accounts'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
			var d  = locals[cdt][cdn];
			return {
				filters: {
					'account_type': 'Payable',
					'company': d.company,
					"is_group": 0
				}
			};
		};
	},
	refresh: function(frm) {
		// read-only for root supplier group
		frm.set_root_read_only("parent_supplier_group");
	}
});