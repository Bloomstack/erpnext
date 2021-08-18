// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('Quoting Sheet', {
	onload: (frm) => {
		frm.set_query("quote_to", function() {
			return{
				"filters": {
					"name": ["in", ["Customer", "Lead"]],
				}
			};
		});

		frm.set_query("bom", () => {
			if (frm.doc.item_code) {
				return {
					filters: {
						"item": frm.doc.item_code
					}
				};
			}
		});
	},

	refresh:(frm) => {
		frm.trigger('set_dynamic_field_label');
	},

	quote_to:(frm) => {
		frm.trigger('set_dynamic_field_label');
	},

	set_dynamic_field_label: function(frm){
		if (frm.doc.quote_to == "Customer")
		{
			frm.set_df_property("party_name", "label", "Customer");
			frm.fields_dict.party_name.get_query = null;
		}

		if (frm.doc.quote_to == "Lead")
		{
			frm.set_df_property("party_name", "label", "Lead");

			frm.fields_dict.party_name.get_query = function() {
				return{	query: "erpnext.controllers.queries.lead_query" };
			};
		}
	},

	qty: (frm) => {
		if (frm.doc.qty) {
			frappe.call({
				method: "set_raw_materials_qty_against_quoting_qty",
				doc: frm.doc,
				callback: () => {
					frm.refresh_fields();
				},
			});
		}
	},

	bom: function (frm) {
		if (frm.doc.bom) {
			frappe.call({
				method: "get_raw_materials",
				doc: frm.doc,
				callback: () => {
					frm.refresh_field("raw_material_items");
					frm.refresh_field("rm_cost");
					frm.refresh_field("qty");
				},
			});
		}
	},
	bulk_discount_scheme: function (frm) {
		if (frm.doc.bulk_discount_scheme) {
			frappe.call({
				method: "get_bulk_discount",
				doc: frm.doc,
				callback: () => {
					frm.refresh_field("bulk_discount");
				},
			});
		}
	},

	update_rate: function (frm) {
		frappe.call({
			method: "erpnext.selling.doctype.quoting_sheet.quoting_sheet.update_latest_rate",
			args: {
				"docname": frm.doc.name
			},
			callback: () => {
				frm.reload_doc();
			},
		});
	},

	calculate_total_raw_material_cost: function (frm) {
		frappe.call({
			method: "calculate_total_raw_material_cost",
			doc: frm.doc,
			callback: (res) => {
				if (res.message) {
					frm.set_value("rm_cost", res.message);
					frm.refresh_field("rm_cost");
				}

			}
		});
	},
});

frappe.ui.form.on("Quoting Sheet Item", {
	item_code: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.item_code) { return; }
		frappe.call({
			method: "erpnext.selling.doctype.quoting_sheet.quoting_sheet.get_item_details_quoting_sheet",
			args: {
				"item_code": row.item_code
			},
			callback: (res) => {
				frappe.model.set_value(cdt, cdn, "rate", res.message.valuation_rate);
				frappe.model.set_value(cdt, cdn, "bom_no", res.message.default_bom);
				frappe.model.set_value(cdt, cdn, "uom", res.message.stock_uom);
			},
		});
	},

	qty: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.qty && row.rate) {
			let amount = row.qty * row.rate;
			frappe.model.set_value(cdt, cdn, "amount", amount);
			frm.trigger("calculate_total_raw_material_cost");
		}
	},

	rate: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.qty && row.rate) {
			let amount = row.qty * row.rate;
			frappe.model.set_value(cdt, cdn, "amount", amount);
			frm.trigger("calculate_total_raw_material_cost");
		}
	},

	customer_provided_item: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.customer_provided_item) {
			frappe.model.set_value(cdt, cdn, "rate", 0.0);
			frappe.model.set_value(cdt, cdn, "amount", 0.0);
		}
		else {
			frappe.call({
				method: "erpnext.selling.doctype.quoting_sheet.quoting_sheet.get_item_details_quoting_sheet",
				args: {
					"item_code": row.item_code
				},
				callback: (res) => {
					frappe.model.set_value(cdt, cdn, "rate", res.message.valuation_rate);
					frm.trigger("qty", cdt, cdn);
				}
			});
		}
	}
});