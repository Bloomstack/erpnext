// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("contract", "terms", "contract_terms");

frappe.ui.form.on('Contract', {
	refresh: function(frm) {

	}
});
