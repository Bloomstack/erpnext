// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.support");

frappe.ui.form.on("Warranty Claim", {
	setup: function(frm) {
		frm.set_query('contact_person', erpnext.queries.contact_query);
		frm.set_query('customer_address', erpnext.queries.address_query);
		frm.set_query('customer', erpnext.queries.customer);
		frm.set_query('serial_no', () => {
			if (frm.doc.customer) {
				return {
					filters: [
						["Serial No", "customer", "=", frm.doc.customer]
					]
				};
			}
		});
	},
	serial_no: function(frm) {
		if (!frm.doc.serial_no) {
			return;
		}
		frappe.call({
			"method": "erpnext.support.doctype.warranty_claim.warranty_claim.get_serial_no_values",
			"args" : {
				"serial_no": frm.doc.serial_no
			},
			callback: function(res) {
				if(res.message) {
					for (let key in res.message) {
						frm.set_value(key, res.message[key]);
					}
				}
			}
		});
	},

	onload: function(frm) {
		if(!frm.doc.status) {
			frm.set_value('status', 'Open');
		}
	},
	customer: function(frm) {
		erpnext.utils.get_party_details(frm);
	},
	customer_address: function(frm) {
		erpnext.utils.get_address_display(frm);
	},
	contact_person: function(frm) {
		erpnext.utils.get_contact_details(frm);
	}
});

erpnext.support.WarrantyClaim = frappe.ui.form.Controller.extend({
	refresh: function() {
		frappe.dynamic_link = {doc: this.frm.doc, fieldname: 'customer', doctype: 'Customer'}

		if(!cur_frm.doc.__islocal &&
			(cur_frm.doc.status=='Open' || cur_frm.doc.status == 'Work In Progress')) {
			cur_frm.add_custom_button(__('Maintenance Visit'),
				this.make_maintenance_visit);
		}
	},

	make_maintenance_visit: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.support.doctype.warranty_claim.warranty_claim.make_maintenance_visit",
			frm: cur_frm
		})
	}
});

$.extend(cur_frm.cscript, new erpnext.support.WarrantyClaim({frm: cur_frm}));

cur_frm.fields_dict['serial_no'].get_query = function(doc, cdt, cdn) {
	let filter = [];

	if(doc.item_code) {
		filter.push(['Serial No', 'item_code', '=', doc.item_code]);
	}

	if(doc.customer) {
		filter.push(['Serial No', 'customer', '=', doc.customer]);
	}
	return {
		filters: filter
	}
}

cur_frm.fields_dict['item_code'].get_query = function(doc, cdt, cdn) {
	if(doc.serial_no) {
		return{
			doctype: "Serial No",
			fields: "item_code",
			filters:{
				name: doc.serial_no
			}
		}
	}
	else{
		return{
			filters:[
				['Item', 'docstatus', '!=', 2],
				['Item', 'disabled', '=', 0]
			]
		}
	}
};