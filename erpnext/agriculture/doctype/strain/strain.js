// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.provide("erpnext.strain");

frappe.ui.form.on('Strain', {
	setup: function (frm) {
		frm.make_methods = {
			'Plant Batch': () => frappe.model.open_mapped_doc({
				method: "erpnext.agriculture.doctype.strain.strain.make_plant_batch",
				frm: frm
			})
		}
	},

	refresh: function(frm) {
		frm.set_query("item_code", "materials_required", function() {
			return {
				query: "erpnext.controllers.queries.item_query"
			};
		});
		frm.fields_dict.materials_required.grid.set_column_disp('bom_no', false);
	},

	onload_post_render: function(frm) {
		frm.get_field("materials_required").grid.set_multiple_add("item_code", "qty");
	}
});


frappe.ui.form.on("BOM Item", {
	item_code: (frm, cdt, cdn) => {
		erpnext.strain.update_item_rate_uom(frm, cdt, cdn);
	},
	qty: (frm, cdt, cdn) => {
		erpnext.strain.update_item_qty_amount(frm, cdt, cdn);
	},
	rate: (frm, cdt, cdn) => {
		erpnext.strain.update_item_qty_amount(frm, cdt, cdn);
	}
});

erpnext.strain.update_item_rate_uom = function(frm, cdt, cdn) {
	frm.doc.materials_required.forEach((item, index) => {
		if (item.name == cdn && item.item_code){
			frappe.call({
				method:'erpnext.agriculture.doctype.strain.strain.get_item_details',
				args: {
					item_code: item.item_code
				},
				callback: (r) => {
					frappe.model.set_value('BOM Item', item.name, 'uom', r.message.uom);
					frappe.model.set_value('BOM Item', item.name, 'rate', r.message.rate);
				}
			});
		}
	});
};

erpnext.strain.update_item_qty_amount = function(frm, cdt, cdn) {
	frm.doc.materials_required.forEach((item, index) => {
		if (item.name == cdn){
			if (!frappe.model.get_value('BOM Item', item.name, 'qty'))
				frappe.model.set_value('BOM Item', item.name, 'qty', 1);
			frappe.model.set_value('BOM Item', item.name, 'amount', item.qty * item.rate);
		}
	});
};