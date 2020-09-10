// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.cscript.refresh = cur_frm.cscript.inspection_type;

frappe.ui.form.on("Quality Inspection", {
	item_code: function (frm) {
		if (frm.doc.item_code) {
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
	check_compliance_item: function (frm) {
		frappe.db.get_value("Item", { "item_code": frm.doc.item_code }, "is_compliance_item")
			.then(item => {
				frm.toggle_reqd('certificate_of_analysis', item.message.is_compliance_item);
				frm.toggle_display('thc', item.message.is_compliance_item);
				frm.toggle_display('cbd', item.message.is_compliance_item);
			})
	},
	inspection_by: function (frm) {
		if (frm.doc.item_code && frm.doc.inspection_by == "External") {
			frm.trigger("check_compliance_item");
		}
		else {
			frm.toggle_reqd('certificate_of_analysis', 0);
			frm.toggle_display('thc', 0);
			frm.toggle_display('cbd', 0);
		}
	},
	package_tag: (frm) => {
		// set package tag from the selected batch, even if empty
		if (frm.doc.package_tag) {
			frappe.db.get_value("Package Tag", frm.doc.package_tag, "batch_no", (r) => {
				frm.set_value("batch_no", r.batch_no);
			});
		}
	},
})

frappe.ui.form.on("Quality Inspection Reading", {
	status: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.status === "Rejected") {
			frappe.confirm(__("This will mark the Quality Inspection as 'Rejected'. Are you sure you want to proceed?"),
				() => { frm.set_value("status", row.status); },
				() => { frappe.reload_doc() }
			);
		}
	}
})

// item code based on GRN/DN
cur_frm.fields_dict['item_code'].get_query = function (doc, cdt, cdn) {
	let doctype;
	if (doc.reference_type == "Stock Entry") {
		doctype = "Stock Entry Detail";
	} else if (doc.reference_type == "Job Card") {
		doctype = "Job Card";
	} else {
		doctype = doc.reference_type + " Item";
	}

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
		};
	}
	return { filters: filters };
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
