// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on('Sales Person', {
	refresh: function(frm) {
		// read-only for root sales group
		frm.set_root_read_only("parent_sales_person");
		if(frm.doc.__onload && frm.doc.__onload.dashboard_info) {
			var info = frm.doc.__onload.dashboard_info;
			frm.dashboard.add_indicator(__('Total Contribution Amount: {0}',
				[format_currency(info.allocated_amount, info.currency)]), 'blue');
		}
	},

	employee: function(frm) {
		frm.toggle_enable("sales_person_name", !frm.doc.employee);
		if (!frm.doc.employee) {
			frm.set_value("sales_person_name", "");
		}
	},

	setup: function(frm) {
		frm.set_query('parent_sales_person', function() {
			return {
				filters: {
					is_group: 1,
					name: ["!=", frm.doc.sales_person_name]
				}
			};
		});

		frm.set_query('employee', function() {
			return {
				query:  "erpnext.controllers.queries.employee_query",
			};
		});

		frm.set_query('distribution_id', 'targets', function(doc, cdt, cdn) {
			let row  = locals[cdt][cdn];
			return {
				filters: {
					fiscal_year: row.fiscal_year
				}
			};
		});

		frm.make_methods = {
			'Sales Order': () => frappe.new_doc("Sales Order")
				.then(() => frm.add_child("sales_team", {"sales_person": frm.doc.name}))
		}
	}
});
