// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Recall Notice', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1) {
			frm.add_custom_button(__("Receive Inventory"), function() {
				frappe.call({
					method: "erpnext.stock.doctype.product_recall_notice.product_recall_notice.create_stock_entry_from_product_recall_notice",
					freeze: true,
					args: {
						"product_recall_notice": frm.doc
					},
					callback: function(res) {
						if(res.message) {
							frappe.msgprint(__(`Stock Entry created ${res.message.stock_entry}`));
						}
					}
				});
			});
		}
	}
});
