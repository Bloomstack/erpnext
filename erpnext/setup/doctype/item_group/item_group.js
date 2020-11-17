// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Item Group", {
	onload: function(frm) {
		frm.list_route = "Tree/Item Group";

		//get query select item group
		frm.set_query('parent_item_group', function() {
			return {
				filters: {
					is_group: 1,
					name: ["!=", frm.doc.item_group_name]
				}
			};
		});

		frm.set_query('expense_account', 'item_group_defaults', function(doc, cdt, cdn) {
			let row  = locals[cdt][cdn];
			return {
				query: "erpnext.controllers.queries.get_expense_account",
				filters: { company: row.company }
			};
		});

		frm.set_query('income_account', 'item_group_defaults', function(doc, cdt, cdn) {
			let row  = locals[cdt][cdn];
			return {
				query: "erpnext.controllers.queries.get_income_account",
				filters: { company: row.company }
			};
		});

		frm.set_query('buying_cost_center', 'item_group_defaults', function(doc, cdt, cdn) {
			let row  = locals[cdt][cdn];
			return {
				filters: {
					is_group: 0,
					company: row.company
				}
			};
		});

		frm.set_query('selling_cost_center', 'item_group_defaults', function(doc, cdt, cdn) {
			let row  = locals[cdt][cdn];
			return {
				filters: {
					is_group: 0,
					company: row.company
				}
			};
		});
	},

	refresh: function(frm) {
		// read-only for root item group
		frm.set_root_read_only("parent_item_group");
		frm.add_custom_button(__("Item Group Tree"), function() {
			frappe.set_route("Tree", "Item Group");
		});

		if(!frm.is_new()) {
			frm.add_custom_button(__("Items"), function() {
				frappe.set_route("List", "Item", {"item_group": frm.doc.name});
			});
		}
	},

	page_name: frappe.utils.warn_page_name_change
});
