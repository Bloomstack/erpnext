/* global frappe, erpnext, __ */

// Copyright (c) 2020, Bloom Stack, Inc and contributors
// For license information, please see license.txt

frappe.ui.form.on("Waste Disposal", {
	setup: function(frm) {
		erpnext.queries.setup_queries(frm, "Warehouse", function() {
			return erpnext.queries.warehouse(frm.doc);
		});
	},

	refresh: function(frm) {
		// Add button to retrieve items for disposal
		if (frm.doc.docstatus < 1) {
			frm.add_custom_button(__("Get Items from Warehouse"), function () {
				frm.events.get_items(frm);
			});
		}

		frm.set_query("item_code", "items", (frm, cdt, cdn) => {
			return erpnext.queries.item({ is_stock_item: 1 });
		});

		frm.set_query("package_tag", "items", (frm, cdt, cdn) => {
			let row = locals[cdt][cdn];

			if (!row.item_code) {
				frappe.throw(__("Please select an Item."));
			}

			return {
				filters: {
					item_code: row.item_code
				}
			};
		});

		frm.set_query("batch_no", "items", (frm, cdt, cdn) => {
			let row = locals[cdt][cdn];

			if (!row.item_code) {
				frappe.throw(__("Row #{0}: Please select an Item.", [row.idx]));
			}

      		if (!row.warehouse) {
				frappe.throw(__("Row #{0}: Please select a warehouse.", [row.idx]));
			}

			return {
				query : "erpnext.controllers.queries.get_batch_no",
				filters: {
					warehouse: row.warehouse,
					item_code: row.item_code
				}
			};
		});
	},

	get_items: function (frm) {
		frappe.prompt({
			label: "Warehouse",
			fieldname: "warehouse",
			fieldtype: "Link",
			options: "Warehouse",
			default: frm.doc.s_warehouse,
			reqd: 1
		},
		function (data) {
			frappe.call({
				method: "erpnext.compliance.doctype.waste_disposal.waste_disposal.get_items",
				args: {
					warehouse: data.warehouse,
					posting_date: frm.doc.disposal_date || frappe.datetime.now_date(),
					posting_time: frm.doc.disposal_time || frappe.datetime.now_time(),
					company: frappe.boot.sysdefaults.company
				},
				callback: function (r) {
					frm.clear_table("items");
					for (let item of r.message) {
						frm.add_child("items", item);
					}
					frm.refresh_field("items");
				}
			});
		}, __("Get Items from Warehouse"), __("Update"));
	}
});


frappe.ui.form.on("Waste Disposal Item", {
	items_add: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (!row.warehouse) {
			row.warehouse = frm.doc.s_warehouse;
		}
	},
	batch_no: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.batch_no && !row.coa_batch_no) {
			frappe.model.get_value("Batch", {"name": row.batch_no}, "coa_batch", (r) => {
				frappe.model.set_value(cdt, cdn, "coa_batch_no", r.coa_batch);
			});
		}
	}
});
