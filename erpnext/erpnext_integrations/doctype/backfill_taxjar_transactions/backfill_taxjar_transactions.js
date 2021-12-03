// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Backfill TaxJar Transactions', {
	push_transaction: (frm) => {
		frm.call('push_transaction').then(r => {
			if (r.message.total_transactions > 0 && r.message.total_transactions === r.message.backfilled_transactions){
				frappe.msgprint(__("Backfilled Transaction Completed. <br>Total Transactions: {0}. <br> Backfilled Transactions: {1}",
				[r.message.total_transactions, r.message.backfilled_transactions]));
				frm.set_value("status", 'Successful');
			}
			else if(r.message.total_transactions > 0 && r.message.backfilled_transactions < r.message.total_transactions){
				frappe.msgprint(__("Backfilled Transaction Paratially Completed. <br>Total Transactions: {0}. <br> Backfilled Transactions: {1}",
				[r.message.total_transactions, r.message.backfilled_transactions]));
				frm.set_value("status", 'Partially Successful');
			}
			else {
				frappe.msgprint(__("Backfilled Transaction failed or There is no transaction availibe for this date range"));
				frm.set_value("status", 'Failed');
			}
		});
	}
});
