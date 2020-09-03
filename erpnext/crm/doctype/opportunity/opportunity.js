// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

{% include 'erpnext/selling/sales_common.js' %}


frappe.ui.form.on("Opportunity", {
	setup: function (frm) {
		frm.email_field = "contact_email";
		frm.make_methods = {
			'Quotation': () => frappe.model.open_mapped_doc({
				method: "erpnext.crm.doctype.opportunity.opportunity.make_quotation",
				frm: frm
			}),
			'Supplier Quotation': () => frappe.model.open_mapped_doc({
				method: "erpnext.crm.doctype.opportunity.opportunity.make_supplier_quotation",
				frm: frm
			}),
			'Investor': () => frappe.model.open_mapped_doc({
				method: "erpnext.crm.doctype.opportunity.opportunity.make_investor",
				frm: frm
			})
		};

		frm.set_query("opportunity_from", function () {
			return { "filters": { "name": ["in", ["Customer", "Lead"]] } }
		});

		if (frm.doc.opportunity_from && frm.doc.party_name) {
			frm.trigger('set_contact_link');
		}

		frm.trigger("toggle_fee_display");
	},

	onload: function (frm) {
		if (!frm.doc.status) {
			frm.set_value('status', 'Open');
		}

		if (!frm.doc.company && frappe.defaults.get_user_default("Company")) {
			frm.set_value('company', frappe.defaults.get_user_default("Company"));
		}

		if (!frm.doc.currency) {
			frm.set_value('currency', frappe.defaults.get_user_default("Currency"));
		}

		frm.trigger("setup_queries");
	},

	refresh: function (frm) {
		frm.toggle_reqd("items", !!frm.doc.with_items);
		frm.events.opportunity_from(frm);
		erpnext.toggle_naming_series();

		if (!frm.is_new()) {
			if (!["Lost", "Quotation"].includes(frm.doc.status)) {
				frm.add_custom_button(__('Lost'), function () {
					frm.trigger('set_as_lost_dialog');
				});
			}

			if (frm.perm[0].write && frm.doc.docstatus === 0) {
				if (frm.doc.status === "Open") {
					frm.add_custom_button(__("Close"), function () {
						frm.set_value("status", "Closed");
						frm.save();
					});
				} else {
					frm.add_custom_button(__("Reopen"), function () {
						frm.set_value("status", "Open");
						frm.save();
					});
				}
			}
		}
	},

	onload_post_render: function(frm) {
		frm.get_field("items").grid.set_multiple_add("item_code", "qty");
	},

	setup_queries: function (frm) {
		if (frm.fields_dict.contact_by.df.options.match(/^User/)) {
			frm.set_query("contact_by", erpnext.queries.user);
		}

		frm.set_query('contact_person', erpnext.queries['contact_query']);
		frm.set_query('customer_address', erpnext.queries.address_query);
		frm.set_query("item_code", "items", function () {
			return {
				query: "erpnext.controllers.queries.item_query",
				filters: { 'is_sales_item': 1 }
			};
		});

		if (frm.doc.opportunity_from == "Lead") {
			frm.set_query('party_name', erpnext.queries['lead']);
		} else if (frm.doc.opportunity_from == "Customer") {
			frm.set_query('party_name', erpnext.queries['customer']);
		}
	},

	party_name: function(frm) {
		frm.toggle_display("contact_info", frm.doc.party_name);
		frm.trigger('set_contact_link');

		if (frm.doc.opportunity_from == "Customer") {
			erpnext.utils.get_party_details(frm);
		} else if (frm.doc.opportunity_from == "Lead") {
			erpnext.utils.map_current_doc({
				method: "erpnext.crm.doctype.lead.lead.make_opportunity",
				source_name: frm.doc.party_name,
				frm: frm
			});
		}
	},

	with_items: function(frm) {
		frm.trigger("toggle_fee_display");
		frm.toggle_reqd("items", !!frm.doc.with_items);
		if (frm.doc.with_items === 1) {
			frm.trigger("calculate_amount");
		} else {
			frm.trigger("calculate_opportunity_cost");
		}
	},

	customer_address: function(frm, cdt, cdn) {
		erpnext.utils.get_address_display(frm, 'customer_address', 'address_display', false);
	},

	contact_person: erpnext.utils.get_contact_details,

	opportunity_from: function(frm) {
		frm.toggle_reqd("party_name", frm.doc.opportunity_from);
		frm.trigger("set_dynamic_field_label");
		frm.trigger("setup_queries");
	},

	service_fee: function (frm) {
		frm.trigger("calculate_opportunity_cost");
	},

	software_fee: function (frm) {
		frm.trigger("calculate_opportunity_cost");
	},

	calculate_amount: function (frm) {
		let total_amount = 0;
		if (frm.doc.items) {
			frm.doc.items.forEach(item => {
				let amount = flt(item.qty) * flt(item.rate);
				frappe.model.set_value(item.doctype, item.name, 'amount', amount);
				total_amount += amount;
			})
		}
		frm.set_value("opportunity_amount", total_amount);
	},

	calculate_opportunity_cost: function (frm) {
		let amount = flt(frm.doc.service_fee) + flt(frm.doc.software_fee);
		frm.set_value("opportunity_amount", amount);
	},

	set_contact_link: function (frm) {
		if (frm.doc.opportunity_from == "Customer" && frm.doc.party_name) {
			frappe.dynamic_link = { doc: frm.doc, fieldname: 'party_name', doctype: 'Customer' }
		} else if (frm.doc.opportunity_from == "Lead" && frm.doc.party_name) {
			frappe.dynamic_link = { doc: frm.doc, fieldname: 'party_name', doctype: 'Lead' }
		}
	},

	set_dynamic_field_label: function (frm) {
		if (frm.doc.opportunity_from) {
			frm.set_df_property("party_name", "label", frm.doc.opportunity_from);
		}
	},

	toggle_fee_display: function (frm) {
		frm.toggle_display('service_fee', !frm.doc.with_items);
		frm.toggle_display('software_fee', !frm.doc.with_items);
	}
})

frappe.ui.form.on("Opportunity Item", {
	item_code: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.item_code) {
			return frappe.call({
				method: "erpnext.crm.doctype.opportunity.opportunity.get_item_details",
				args: { "item_code": row.item_code },
				callback: function (r, rt) {
					if (r.message) {
						$.each(r.message, function (k, v) {
							frappe.model.set_value(cdt, cdn, k, v);
						});
						refresh_field('image_view', row.name, 'items');
					}
				}
			})
		}
	},

	qty: function (frm) {
		frm.trigger("calculate_amount");
	},

	rate: function (frm) {
		frm.trigger("calculate_amount");
	},

	items_remove: function (frm) {
		frm.trigger("calculate_amount");
	}
})