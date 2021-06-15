// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("contract_template", "contract_terms", "contract_terms");
cur_frm.add_fetch("contract_template", "requires_fulfilment", "requires_fulfilment");

// Add fulfilment terms from contract template into contract
frappe.ui.form.on("Contract", {
	onload: (frm) => {
		// Setting company field as Empty by default (Only for draft Contracts),
		// so that it only populates on submit
		if (frm.doc.docstatus == 0) {
			frm.set_value("company", "");
		}
	},
	refresh: (frm) => {
		frm.set_query("contract_template", () => {
			return {
				filters: {
					"company": frm.doc.company
				}
			};
		});
		// pull users for the set party
		frm.set_query("party_user", (doc) => {
			return {
				query: "erpnext.crm.doctype.contract.contract.get_party_users",
				filters: {
					"party_type": doc.party_type,
					"party_name": doc.party_name
				}
			}
		});

		if (frm.doc.docstatus === 1 && !frm.doc.customer_signature) {
			frm.add_custom_button(__("Authorize"), () => {
				frappe.prompt([
					{
						"label": "Contact Email",
						"fieldtype": "Data",
						"options": "Email",
						"fieldname": "contact_email",
						"default": frm.doc.party_user,
						"reqd": 1
					},
					{
						"label": "Contact Person",
						"fieldtype": "Data",
						"fieldname": "contact_person",
						"default": frm.doc.party_name,
						"reqd": 1
					}
				],
				function (data) {
					frappe.call({
						method: "erpnext.utils.create_authorization_request",
						args: {
							dt: frm.doc.doctype,
							dn: frm.doc.name,
							contact_email: data.contact_email,
							contact_name: data.contact_person
						},
						callback: (r) => {
							if (!r.exc) {
								frappe.msgprint(__(`${frm.doc.name} has been successfully sent to ${data.contact_email}`))
							}
						}
					})
				},
				__("Send Authorization Request"))
			}).addClass("btn-primary");
		}
	},

	before_submit: (frm) => {
		if(!frm.doc.signee_company) {
			frm.scroll_to_field('signee_company');
			frappe.throw("Please sign the contract before submiting it.")
		}
	},

	signee_company: (frm) =>{
		frm.set_value("signed_by_company_date", frappe.datetime.nowdate());
	},

	party_name: (frm) => {
		if (frm.doc.party_type == 'Employee' && frm.doc.party_name) {
			frappe.db.get_value("Employee", { "name": frm.doc.party_name }, "employee_name", (r) => {
				if (r && r.employee_name) {
					frm.set_value("employee_name", r.employee_name);
				} else {
					frm.set_value("employee_name", null);
				}
			})
		} else {
			frm.set_value("employee_name", null);
		}
	},

	contract_template: function (frm) {
		// Populate the fulfilment terms table from a contract template, if any
		if (frm.doc.contract_template) {
			frappe.model.with_doc("Contract Template", frm.doc.contract_template, function () {
				let tabletransfer = frappe.model.get_doc("Contract Template", frm.doc.contract_template);

				// populate contract sections table
				frm.doc.contract_sections = [];
				$.each(tabletransfer.contract_sections, function (index, row) {
					let d = frm.add_child("contract_sections");
					d.section = row.section;
					d.description = row.description;
					frm.refresh_field("contract_sections");
				});

				// populate fulfilment terms table
				frm.doc.fulfilment_terms = [];
				$.each(tabletransfer.fulfilment_terms, function (index, row) {
					let d = frm.add_child("fulfilment_terms");
					d.requirement = row.requirement;
					frm.refresh_field("fulfilment_terms");
				});
			});
		}
	}
});
