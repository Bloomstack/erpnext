// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Backfill TaxJar Transactions', {
	refresh: (frm) => {
		if (!frm.is_new() && frm.doc.status === "Not Started") {
			frm.add_custom_button(__('Push Transactions'), function() {
				frm.call('push_transaction').then(r => {
					if (r.message.total_transactions > 0 && r.message.total_transactions === r.message.backfilled_transactions){
						frappe.msgprint(__("Backfilled Transaction Completed. <br>Total Transactions: {0}. <br> Backfilled Transactions: {1}",
							[r.message.total_transactions, r.message.backfilled_transactions]));
						frm.set_value("status", 'Completed');
						frm.save();
					}
					else if(r.message.total_transactions > 0 && r.message.backfilled_transactions < r.message.total_transactions){
						frappe.msgprint(__("Backfilled Transaction Paratially Completed. <br>Total Transactions: {0}. <br> Backfilled Transactions: {1}",
							[r.message.total_transactions, r.message.backfilled_transactions]));
						frm.set_value("status", 'Partially Completed');
						frm.save();
					}
					else {
						frappe.msgprint(__("Backfilled Transaction failed or There is no transaction availibe for this date range"));
						frm.set_value("status", 'Failed');
						frm.save();
					}
				});
			}).addClass("btn-primary");
		}
		frm.events.setup_progress(frm);
	},
	setup_progress: function (frm) {
		frappe.realtime.on('backfill_taxjar_transactions', (data) => {
			if (data.progress) {
				frm.dashboard.show_progress('Backfill TaxJar Transaction', data.progress / data.total * 100, data.label);
				if (data.progress === data.total) {
					frm.dashboard.hide_progress('Backfill TaxJar Transaction');
					frm.refresh();
				}
			}
		});
	},
});
