// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.cscript.refresh = cur_frm.cscript.inspection_type;

frappe.ui.form.on("Quality Inspection", {
	item_code: function (frm) {
		if (frm.doc.item_code) {
			if (["Purchase Invoice", "Purchase Receipt"].includes(frm.doc.reference_type)) {
				if (frm.doc.reference_name) {
					frappe.call({
						method: "erpnext.stock.doctype.quality_inspection.quality_inspection.get_purchase_item_details",
						args: {
							"doctype": frm.doc.reference_type,
							"name": frm.doc.reference_name,
							"item_code": frm.doc.item_code
						},
						callback: function (data) {
							frm.set_value("uom", data.message.uom);
							frm.set_value("qty", data.message.qty);
							frm.set_value("manufacturer_name", data.message.supplier)

							frappe.db.get_value("Supplier", { "supplier_name": data.message.supplier }, "website")
								.then(supplier => {
									if (supplier.message) {
										frm.set_value("manufacturer_website", supplier.message.website);
									}
								})
						}
					})
				}
			}

			frm.trigger("check_compliance_item");
			frappe.db.get_value('Item', { name: frm.doc.item_code }, ['has_batch_no', 'has_serial_no'], (r) => {
				frm.toggle_reqd("batch_no", r.has_batch_no);
				frm.toggle_reqd("item_serial_no", r.has_serial_no);
			});

			return frm.call({
				method: "get_quality_inspection_template",
				doc: frm.doc,
				callback: function () {
					refresh_field(['quality_inspection_template', 'readings']);
				}
			});

		}
	},
	quality_inspection_template: function (frm) {
		if (frm.doc.quality_inspection_template) {
			return frm.call({
				method: "get_item_specification_details",
				doc: frm.doc,
				callback: function () {
					refresh_field('readings');
				}
			});
		}
	},
	on_submit: function (frm) {
		if (frm.doc.thc || frm.doc.cbd) {
			frappe.call({
				method: "erpnext.stock.doctype.batch.batch.save_thc_cbd",
				args: {
					"batch_no": frm.doc.batch_no,
					"thc": frm.doc.thc,
					"cbd": frm.doc.cbd
				},
			})
		}
	},
	onload: (frm) => {
		if (frm.doc.item_code) {
			frm.trigger("check_compliance_item");
		}
	},
	check_compliance_item: function (frm) {
		frappe.db.get_value("Compliance Item", { "item_code": frm.doc.item_code }, "item_code")
			.then(item => {
				if (item.message) {
					frm.toggle_reqd('batch_no', true);
					frm.toggle_display('thc', true);
					frm.toggle_display('cbd', true);
				}
				else {
					frm.toggle_reqd('batch_no', false);
					frm.toggle_display('thc', false);
					frm.toggle_display('cbd', false);
				}
			})
	}
})

// item code based on GRN/DN
cur_frm.fields_dict['item_code'].get_query = function (doc, cdt, cdn) {
	const doctype = (doc.reference_type == "Stock Entry") ?
		"Stock Entry Detail" : doc.reference_type + " Item";

	if (doc.reference_type && doc.reference_name) {
		return {
			query: "erpnext.stock.doctype.quality_inspection.quality_inspection.item_query",
			filters: {
				"from": doctype,
				"parent": doc.reference_name,
				"inspection_type": doc.inspection_type
			}
		};
	}
},

	// Serial No based on item_code
	cur_frm.fields_dict['item_serial_no'].get_query = function (doc, cdt, cdn) {
		var filters = {};
		if (doc.item_code) {
			filters = {
				'item_code': doc.item_code
			}
		}
		return { filters: filters }
	}

cur_frm.set_query("batch_no", function (doc) {
	return {
		filters: {
			"item": doc.item_code
		}
	}
})

cur_frm.add_fetch('item_code', 'item_name', 'item_name');
cur_frm.add_fetch('item_code', 'description', 'description');
