// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Backfill TaxJar Transactions', {
	push_transaction: (frm) => {
		frm.call('push_transaction').then(r => {
			if(r.message === 1) {
				frm.refresh();
			}
		});
	}
});
