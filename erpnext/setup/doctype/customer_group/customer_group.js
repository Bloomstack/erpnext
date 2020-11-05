// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Group', {
	setup: function(frm) {
		frm.fields_dict['parent_customer_group'].get_query = function(doc) {
			return {
				filters:[
					['Customer Group', 'is_group', '=', 1],
					['Customer group', 'name', "!=", doc.customer_group_name]
				]
			}
		}
		frm.fields_dict['accounts'].grid.get_field('account').get_query = function(cdt, cdn) {
			var d  = locals[cdt][cdn];
			return {
				filters: {
					'account_type': 'Receivable',
					'company': d.company,
					"is_group": 0
				}
			}
		}
	},
	refresh: function(frm) {
		// read-only for root customer group
		frm.set_root_read_only("parent_customer_group");
	}
});