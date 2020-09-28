frappe.listview_settings['Payment Entry'] = {

	onload: function (listview) {
		listview.page.fields_dict.party_type.get_query = function () {
			return {
				"filters": {
					"name": ["in", Object.keys(frappe.boot.party_account_types)],
				}
			};
		};
		listview.page.add_actions_menu_item(__('Set Cheque Numbers'), () => {
			const selected_docs = listview.get_checked_items();
			const doctype = listview.doctype;
			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (doc.docstatus !== 0) {
						frappe.throw(__("Cannot print Cheques for 'Submitted' or 'Cancelled' documents"));
					}
					if (doc.mode_of_payment !== "Check") {
						frappe.throw(__("{0}: The mode of payment should be 'Check'",
							[doc.title])
						);
					}
				}
				let d = new frappe.ui.Dialog({
					title: 'Enter Cheque numbers',
					fields: [
						{
							label: 'Starting Cheque Number',
							fieldname: 'starting_cheque_number',
							fieldtype: 'Int',
							reqd: 1
						}
					],
					primary_action_label: 'Submit',
					primary_action(values) {
						frappe.call({
							method: "erpnext.accounts.doctype.payment_entry.payment_entry.init_print_cheque",
							args: { "start": values.starting_cheque_number, "selected_docs": selected_docs, "doctype": doctype },
							callback: function (r) {
								let data = [];
								r.message.forEach(element => {
									data.push(element["name"] + " : " + element["series"]);
								});
								frappe.msgprint(__("Cheques have been assigned to the selected payments:<br><ul><li>{0}</li></ul>", [data.join("<br><li>")]));
							}
						});
						d.hide();
					}
				});
				d.show();
			}
		}, false);
	}

};