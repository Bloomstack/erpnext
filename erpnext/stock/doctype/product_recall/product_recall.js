// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Recall', {
	// refresh: function(frm) {

	// }
	onload: function(frm) {
		frm.set_query('batch_no', function(doc) {
			return {
				filters: {
					"batch_qty": [">", 0]
				}
			};
		});
	},
});
