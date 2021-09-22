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
