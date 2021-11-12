frappe.listview_settings['Purchase Order'] = {
	add_fields: ["base_grand_total", "company", "currency", "supplier",
		"supplier_name", "per_received", "per_billed", "status"],
	get_indicator: function (doc) {
		if (doc.status === "Closed") {
			return [__("Closed"), "green", "status,=,Closed"];
		} else if (doc.status === "On Hold") {
			return [__("On Hold"), "orange", "status,=,On Hold"];
		} else if (doc.status === "Delivered") {
			return [__("Delivered"), "green", "status,=,Closed"];
		} else if (flt(doc.per_received, 2) < 100 && doc.status !== "Closed") {
			if (flt(doc.per_billed, 2) < 100) {
				return [__("To Receive and Bill"), "orange",
					"per_received,<,100|per_billed,<,100|status,!=,Closed"];
			} else {
				return [__("To Receive"), "orange",
					"per_received,<,100|per_billed,=,100|status,!=,Closed"];
			}
		} else if (flt(doc.per_received, 2) >= 100 && flt(doc.per_billed, 2) < 100 && doc.status !== "Closed") {
			return [__("To Bill"), "orange", "per_received,=,100|per_billed,<,100|status,!=,Closed"];
		} else if (flt(doc.per_received, 2) >= 100 && flt(doc.per_billed, 2) == 100 && doc.status !== "Closed") {
			return [__("Completed"), "green", "per_received,=,100|per_billed,=,100|status,!=,Closed"];
		}
	},
	onload: function (listview) {
		var method = "erpnext.buying.doctype.purchase_order.purchase_order.close_or_unclose_purchase_orders";

		listview.page.add_menu_item(__("Close"), function () {
			listview.call_for_selected_items(method, { "status": "Closed" });
		});

		listview.page.add_menu_item(__("Re-open"), function () {
			listview.call_for_selected_items(method, { "status": "Submitted" });
		});

		const create_purchase_invoice_action = () => {
			const selected_docs = listview.get_checked_items();
			const docnames = listview.get_checked_items(true);

			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1 || ["On Hold", "Closed"].includes(doc.status)) {
						frappe.throw(__("Cannot create a Purchase Invoice from {0} orders", [doc.status.bold()]));
					}
				}

				frappe.confirm(__(`This will create a Purchase Invoice for each Purchase Order.<br><br>
					Are you sure you want to create {0} Purchase Invoice(s)?`, [selected_docs.length]),
				() => {
					frappe.call({
						method: "erpnext.buying.doctype.purchase_order.purchase_order.create_multiple_purchase_invoices",
						args: {
							"orders": docnames
						},
						freeze: true,
						callback: (r) => {
							if (!r.exc) {
								if (r.message.length === 0) {
									return;
								}

								let message = "";

								// loop through each created order and render linked Purchase Invoices.
								let created_order_message = "";
								let created_orders = r.message.filter(order => order.created === true);
								for (let order of created_orders) {
									let purchase_invoices = order.purchase_invoices
										.map(purchase_invoice => frappe.utils.get_form_link("Purchase Invoice", purchase_invoice, true))
										.join(", ");

									created_order_message += `<li><strong>${order.supplier}</strong> (${order.purchase_order}): ${purchase_invoices}</li>`;
								}

								if (created_order_message) {
									message += `The following Purchase Invoice were created:<br><br><ul>${created_order_message}</ul>`;
								}

								// loop through each existing order and render linked Purchase Invoices
								let existing_order_message = "";
								let existing_orders = r.message.filter(order => order.created === false);
								for (let order of existing_orders) {
									let purchase_invoices = order.purchase_invoices
										.map(purchase_invoice => frappe.utils.get_form_link("Purchase Invoice", purchase_invoice, true))
										.join(", ");

									existing_order_message += `<li><strong>${order.supplier}</strong> (${order.purchase_order}): ${purchase_invoices || "No available items to pick"}</li>`;
								}

								if (existing_order_message) {
									message += `<br>The following orders either have existing Purchase Invoice:<br><br><ul>${existing_order_message}</ul>`;
								}

								frappe.msgprint(__(message));

								// if validation messages are found, append at the bottom of our message
								if (r._server_messages) {
									let server_messages = JSON.parse(r._server_messages);
									for (let server_message of server_messages) {
										frappe.msgprint(__(JSON.parse(server_message).message));
									}
									// delete server messages to avoid Frappe eating up our msgprint
									delete r._server_messages;
								}

								listview.refresh();
							}
						}
					});
				});
			}
		};
		listview.page.add_actions_menu_item(__('Create Purchase Invoices'), create_purchase_invoice_action, false);

		const action = () => {
			const selected_docs = listview.get_checked_items();
			const doctype = listview.doctype;
			if (selected_docs.length > 0) {
				let title = selected_docs[0].title;
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1) {
						frappe.throw(__("Cannot Email Draft or cancelled documents"));
					}
					if (doc.title !== title) {
						frappe.throw(__("Select only one Supplier's purchase orders"));
					}
				}
				frappe.call({
					method: "erpnext.utils.get_contact",
					args: { "doctype": doctype, "name": selected_docs[0].name, "contact_field": "supplier" },
					callback: function (r) {
						frappe.call({
							method: "erpnext.utils.get_document_links",
							args: { "doctype": doctype, "docs": selected_docs },
							callback: function (res) {
								new frappe.views.CommunicationComposer({
									subject: `${frappe.sys_defaults.company} - ${doctype} links`,
									recipients: r.message ? r.message.email_id : null,
									message: res.message,
									doc: {}
								});
							}
						});
					}
				});
			}
		};
		listview.page.add_actions_menu_item(__('Email'), action, true);
	}
};
