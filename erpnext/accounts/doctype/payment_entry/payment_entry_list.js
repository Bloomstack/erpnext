frappe.listview_settings['Payment Entry'] = {

	onload: function (listview) {
		listview.page.fields_dict.party_type.get_query = function () {
			return {
				"filters": {
					"name": ["in", Object.keys(frappe.boot.party_account_types)],
				}
			};
		};
		listview.page.add_actions_menu_item(__('Print Check'), () => {
			const selected_docs = listview.get_checked_items();
			const doctype = listview.doctype;
			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (doc.docstatus !== 0) {
						frappe.throw(__("Cannot print checks for 'Submitted' or 'Cancelled' documents"));
					}
					if (doc.mode_of_payment !== "Check") {
						frappe.throw(__("{0}: The payment mode should be 'Check'",
							[doc.title])
						);
					}
				}
				let d = new frappe.ui.Dialog({
					title: 'Enter details',
					fields: [
						{
							label: 'Starting Check Number',
							fieldname: 'starting_check_number',
							fieldtype: 'Int',
							reqd: 1
						}
					],
					primary_action_label: 'Submit',
					primary_action(values) {
						frappe.call({
							method: "erpnext.accounts.doctype.payment_entry.payment_entry.init_print_check",
							args: { "start": values.starting_check_number, "selected_docs": selected_docs, "doctype": doctype },
							callback: function () {
								frappe.msgprint(__("Checks have been assigned to the selected payments"));
							}
						});
						d.hide();
					}
				});
				d.show();
			}
		}, true);
	}

};