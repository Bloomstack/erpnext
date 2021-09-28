// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Purchase Invoice'] = {
	add_fields: ["supplier", "supplier_name", "base_grand_total", "outstanding_amount", "due_date", "company",
		"currency", "is_return", "release_date", "on_hold"],
	get_indicator: function(doc) {
		if( (flt(doc.outstanding_amount) <= 0) && doc.docstatus == 1 &&  doc.status == 'Debit Note Issued') {
			return [__("Debit Note Issued"), "darkgrey", "outstanding_amount,<=,0"];
		} else if(flt(doc.outstanding_amount) > 0 && doc.docstatus==1) {
			if(cint(doc.on_hold) && !doc.release_date) {
				return [__("On Hold"), "darkgrey"];
			} else if(cint(doc.on_hold) && doc.release_date && frappe.datetime.get_diff(doc.release_date, frappe.datetime.nowdate()) > 0) {
				return [__("Temporarily on Hold"), "darkgrey"];
			} else if(frappe.datetime.get_diff(doc.due_date) < 0) {
				return [__("Overdue"), "red", "outstanding_amount,>,0|due_date,<,Today"];
			} else {
				return [__("Unpaid"), "orange", "outstanding_amount,>,0|due_date,>=,Today"];
			}
		} else if(cint(doc.is_return)) {
			return [__("Return"), "darkgrey", "is_return,=,Yes"];
		} else if(flt(doc.outstanding_amount)==0 && doc.docstatus==1) {
			return [__("Paid"), "green", "outstanding_amount,=,0"];
		}
	}
};

frappe.listview_settings['Purchase Invoice'].onload =
	function (doclist) {
		const action = () => {
			const selected_docs = doclist.get_checked_items();
			const doctype = doclist.doctype;
			if (selected_docs.length > 0) {
				let title = selected_docs[0].title;
				for (let doc of selected_docs) {
					if (doc.docstatus !== 1) {
						frappe.throw(__("Cannot Email Draft or cancelled documents"));
					}
					if (doc.title !== title) {
						frappe.throw(__("Select only one Supplier's purchase invoice"));
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
		doclist.page.add_actions_menu_item(__('Email'), action, true);
	};
