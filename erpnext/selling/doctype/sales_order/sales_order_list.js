frappe.listview_settings['Sales Order'] = {
	add_fields: ["base_grand_total", "customer_name", "currency", "delivery_date",
		"per_delivered", "per_billed", "status", "order_type", "name", "skip_delivery_note", "per_picked"],
	get_indicator: function (doc) {
		if (doc.status === "Closed") {
			// Closed
			return [__("Closed"), "green", "status,=,Closed"];
		} else if (doc.status === "On Hold") {
			// on hold
			return [__("On Hold"), "orange", "status,=,On Hold"];
		} else if (doc.status === "Completed") {
			return [__("Completed"), "green", "status,=,Completed"];
		} else if (!doc.skip_delivery_note && flt(doc.per_delivered, 6) < 100) {
			if (frappe.datetime.get_diff(doc.delivery_date) < 0) {
			// not delivered & overdue
				return [__("Overdue"), "red",
					"per_delivered,<,100|delivery_date,<,Today|status,!=,Closed"];
			} else if (doc.docstatus === 1 && doc.per_billed === 100 && doc.per_picked > 0) {
				return [__("To Pick"), "orange",
					"per_picked,<,100|per_billed,=,100|per_delivered,<,100|status,!=,Closed"];
			} else if (doc.docstatus === 1 && doc.per_billed < 100 && doc.per_picked > 0) {
				return [__("To Pick and Bill"), "orange",
					"per_picked,<,100|per_billed,<,100|per_delivered,<,100|status,!=,Closed"];
			} else if (flt(doc.grand_total) === 0) {
				// not delivered (zero-amount order)
				return [__("To Deliver"), "orange",
					"per_delivered,<,100|grand_total,=,0|status,!=,Closed"];
			} else if (flt(doc.per_billed, 6) < 100) {
				// not delivered & not billed
				return [__("To Deliver and Bill"), "orange",
					"per_delivered,<,100|per_billed,<,100|status,!=,Closed"];
			} else {
				// not billed
				return [__("To Deliver"), "orange",
					"per_delivered,<,100|per_billed,=,100|status,!=,Closed"];
			}
		} else if ((flt(doc.per_delivered, 6) === 100) && flt(doc.grand_total) !== 0
			&& flt(doc.per_billed, 6) < 100) {
			// to bill
			return [__("To Bill"), "orange",
				"per_delivered,=,100|per_billed,<,100|status,!=,Closed"];
		} else if (doc.skip_delivery_note && flt(doc.per_billed, 6) < 100){
			return [__("To Bill"), "orange", "per_billed,<,100|status,!=,Closed"];
		}
	},
	onload: function(listview) {
		var method = "erpnext.selling.doctype.sales_order.sales_order.close_or_unclose_sales_orders";

		listview.page.add_menu_item(__("Close"), function() {
			listview.call_for_selected_items(method, {"status": "Closed"});
		});

		listview.page.add_menu_item(__("Re-open"), function() {
			listview.call_for_selected_items(method, {"status": "Submitted"});
		});

		const create_pick_list_action = () => {
			const selected_docs = listview.get_checked_items();
			const docnames = listview.get_checked_items(true);

			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1 || ["On Hold", "Closed"].includes(doc.status)) {
						frappe.throw(__("Cannot create a Pick List from {0} orders", [doc.status.bold()]));
					}
				}

				frappe.confirm(__(`This will create a Pick List for each Sales Order.<br><br>
					Are you sure you want to create {0} Pick List(s)?`, [selected_docs.length]),
				() => {
					frappe.call({
						method: "erpnext.selling.doctype.sales_order.sales_order.create_multiple_pick_lists",
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

								// loop through each created order and render linked Pick Lists
								let created_order_message = "";
								let created_orders = r.message.filter(order => order.created === true);
								for (let order of created_orders) {
									let pick_lists = order.pick_lists
										.map(pick_list => frappe.utils.get_form_link("Pick List", pick_list, true))
										.join(", ");

									created_order_message += `<li><strong>${order.customer}</strong> (${order.sales_order}): ${pick_lists}</li>`;
								}

								if (created_order_message) {
									message += `The following Pick Lists were created:<br><br><ul>${created_order_message}</ul>`;
								}

								// loop through each existing order and render linked Pick Lists
								let existing_order_message = "";
								let existing_orders = r.message.filter(order => order.created === false);
								for (let order of existing_orders) {
									let pick_lists = order.pick_lists
										.map(pick_list => frappe.utils.get_form_link("Pick List", pick_list, true))
										.join(", ");

									existing_order_message += `<li><strong>${order.customer}</strong> (${order.sales_order}): ${pick_lists || "No available items to pick"}</li>`;
								}

								if (existing_order_message) {
									message += `<br>The following orders either have existing Pick Lists or no items to pick:<br><br><ul>${existing_order_message}</ul>`;
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

		const create_sales_invoice_action = () => {
			const selected_docs = listview.get_checked_items();
			const docnames = listview.get_checked_items(true);

			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1 || ["On Hold", "Closed"].includes(doc.status)) {
						frappe.throw(__("Cannot create a Sales Invoice from {0} orders", [doc.status.bold()]));
					}
				}

				frappe.confirm(__(`This will create a Sales Invoice for each Sales Order.<br><br>
					Are you sure you want to create {0} Sales Invoice(s)?`, [selected_docs.length]),
				() => {
					frappe.call({
						method: "erpnext.selling.doctype.sales_order.sales_order.create_multiple_sales_invoices",
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

								// loop through each created order and render linked Sales Invoices.
								let created_order_message = "";
								let created_orders = r.message.filter(order => order.created === true);
								for (let order of created_orders) {
									let sales_invoices = order.sales_invoices
										.map(sales_invoice => frappe.utils.get_form_link("Sales Invoice", sales_invoice, true))
										.join(", ");

									created_order_message += `<li><strong>${order.customer}</strong> (${order.sales_order}): ${sales_invoices}</li>`;
								}

								if (created_order_message) {
									message += `The following Sales Invoice were created:<br><br><ul>${created_order_message}</ul>`;
								}

								// loop through each existing order and render linked Sales Invoices
								let existing_order_message = "";
								let existing_orders = r.message.filter(order => order.created === false);
								for (let order of existing_orders) {
									let sales_invoices = order.sales_invoices
										.map(delivery_note => frappe.utils.get_form_link("Sales Invoice", delivery_note, true))
										.join(", ");

									existing_order_message += `<li><strong>${order.customer}</strong> (${order.sales_order}): ${sales_invoices || "No available items to pick"}</li>`;
								}

								if (existing_order_message) {
									message += `<br>The following orders either have existing Sales Invoice:<br><br><ul>${existing_order_message}</ul>`;
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

		const create_delivery_note_action = () => {
			const selected_docs = listview.get_checked_items();
			const docnames = listview.get_checked_items(true);

			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1 || ["On Hold", "Closed"].includes(doc.status)) {
						frappe.throw(__("Cannot create a Delivery Note from {0} orders", [doc.status.bold()]));
					}
				}

				frappe.confirm(__(`This will create a Delivery Note for each Sales Order.<br><br>
					Are you sure you want to create {0} Delivery Note(s)?`, [selected_docs.length]),
				() => {
					frappe.call({
						method: "erpnext.selling.doctype.sales_order.sales_order.create_multiple_delivery_notes",
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

								// loop through each created order and render linked Delivery Notes
								let created_order_message = "";
								let created_orders = r.message.filter(order => order.created === true);
								for (let order of created_orders) {
									let delivery_notes = order.delivery_notes
										.map(delivery_note => frappe.utils.get_form_link("Delivery Note", delivery_note, true))
										.join(", ");

									created_order_message += `<li><strong>${order.customer}</strong> (${order.sales_order}): ${delivery_notes}</li>`;
								}

								if (created_order_message) {
									message += `The following Delivery Note were created:<br><br><ul>${created_order_message}</ul>`;
								}

								// loop through each existing order and render linked Delivery Notes
								let existing_order_message = "";
								let existing_orders = r.message.filter(order => order.created === false);
								for (let order of existing_orders) {
									let delivery_notes = order.delivery_notes
										.map(delivery_note => frappe.utils.get_form_link("Delivery Note", delivery_note, true))
										.join(", ");

									existing_order_message += `<li><strong>${order.customer}</strong> (${order.sales_order}): ${delivery_notes || "No available items to pick"}</li>`;
								}

								if (existing_order_message) {
									message += `<br>The following orders either have existing Delivery Note:<br><br><ul>${existing_order_message}</ul>`;
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

		const create_production_plan_action = () => {
			const selected_docs = listview.get_checked_items();
			const docnames = listview.get_checked_items(true);

			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1 || ["On Hold", "Closed"].includes(doc.status)) {
						frappe.throw(__("Cannot create a Production Plan from {0} orders", [doc.status.bold()]));
					}
				}

				frappe.confirm(__(`This will create a Production Plan for each Sales Order.<br><br>
					Are you sure you want to create {0} Production Plan(s)?`, [selected_docs.length]),
				() => {
					frappe.call({
						method: "erpnext.selling.doctype.sales_order.sales_order.create_multiple_production_plans",
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

								// loop through each created order and render linked Production Plans
								let created_order_message = "";
								let created_orders = r.message.filter(order => order.created === true);
								for (let order of created_orders) {
									let production_plans = order.production_plans
										.map(production_plan => frappe.utils.get_form_link("Production Plan", production_plan, true))
										.join(", ");

									created_order_message += `<li><strong>${order.customer}</strong> (${order.sales_order}): ${production_plans}</li>`;
								}

								if (created_order_message) {
									message += `The following Production Plan were created:<br><br><ul>${created_order_message}</ul>`;
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

		const create_one_production_plan_action = () => {
			const selected_docs = listview.get_checked_items();
			const docnames = listview.get_checked_items(true);

			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1 || ["On Hold", "Closed"].includes(doc.status)) {
						frappe.throw(__("Cannot create a Production Plan from {0} orders", [doc.status.bold()]));
					}
				}

				frappe.confirm(__(`This will create a Production Plan against selected Sales Orders.<br>
					Are you sure you want to create Production Plan?`),
				() => {
					frappe.call({
						method: "erpnext.selling.doctype.sales_order.sales_order.create_one_production_plan_from_multiple_sales_orders",
						args: {
							"sales_orders": docnames
						},
						freeze: true,
						callback: (r) => {
							if (!r.exc) {
								if (r.message.length === 0) {
									return;
								}

								let production_plan_link = frappe.utils.get_form_link("Production Plan", r.message, true)
								frappe.msgprint(__(`Production Plan: <b>${production_plan_link}</b> created.`));

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

		listview.page.add_actions_menu_item(__('Create Pick Lists'), create_pick_list_action, false);
		listview.page.add_actions_menu_item(__('Create Production Plan'), create_production_plan_action, false);
		listview.page.add_actions_menu_item(__('Create Single Production Plan'), create_one_production_plan_action, false);
		listview.page.add_actions_menu_item(__('Create Sales Invoices'), create_sales_invoice_action, false);
		listview.page.add_actions_menu_item(__('Create Delivery Note'), create_delivery_note_action, false);

		const send_email_action = () => {
			const selected_docs = listview.get_checked_items();
			const doctype = listview.doctype;
			if (selected_docs.length > 0) {
				let title = selected_docs[0].title;
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1) {
						frappe.throw(__("Cannot Email Draft or cancelled documents"));
					}
					if (doc.title !== title) {
						frappe.throw(__("Select only one customer's sales orders"));
					}
				}
				frappe.call({
					method: "erpnext.utils.get_contact",
					args: { "doctype": doctype, "name": selected_docs[0].name, "contact_field": "customer" },
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
		listview.page.add_actions_menu_item(__('Email'), send_email_action, true);
	}
};
