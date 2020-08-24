// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Investor', {
	setup: function(frm) {
		frm.set_query("investor_from", function() {
			return{
				"filters": {
					"name": ["in", ["Opportunity", "Lead"]],
				}
			};
		});
	},

	refresh: function(frm) {
		frappe.dynamic_link = {doc: frm.doc, fieldname: 'investor_name', doctype: 'Investor'};
		frm.toggle_display(['address_html','contact_html'], !frm.doc.__islocal);

		if(!frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(frm);
			erpnext.utils.set_party_dashboard_indicators(frm);

		} else {
			frappe.contacts.clear_address_and_contact(frm);
		}

	}
});
