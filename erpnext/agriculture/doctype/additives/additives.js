// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Additives', {
	additive_type: (frm) => {
		frm.call('load_contents');
	}
});
