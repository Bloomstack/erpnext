// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Repost Item Valuation', {
	setup: function(frm) {
		frm.set_query("warehouse", () => {
			let filters = {
				'is_group': 0
			};
			if (frm.doc.company) filters['company'] = frm.doc.company;
			return {filters: filters};
		});

		frm.set_query("voucher_type", () => {
			return {
				filters: {
					name: ['in', ['Purchase Receipt', 'Purchase Invoice', 'Delivery Note',
						'Sales Invoice', 'Stock Entry', 'Stock Reconciliation']]
				}
			};
		});

		if (frm.doc.company) {
			frm.set_query("voucher_no", () => {
				return {
					filters: {
						company: frm.doc.company
					}
				};
			});
		}
	}
});
