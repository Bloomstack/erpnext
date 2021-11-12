// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.hr");
erpnext.hr.EmployeeController = frappe.ui.form.Controller.extend({
	setup: function() {
		this.frm.fields_dict.user_id.get_query = function(doc, cdt, cdn) {
			return {
				query: "frappe.core.doctype.user.user.user_query",
				filters: {ignore_user_type: 1}
			}
		}
		this.frm.fields_dict.reports_to.get_query = function(doc, cdt, cdn) {
			return { query: "erpnext.controllers.queries.employee_query"} }
	},

	refresh: function() {
		var me = this;
		erpnext.toggle_naming_series();
	},

	date_of_birth: function() {
		return cur_frm.call({
			method: "get_retirement_date",
			args: {date_of_birth: this.frm.doc.date_of_birth}
		});
	},

	salutation: function() {
		if(this.frm.doc.salutation) {
			this.frm.set_value("gender", {
				"Mr": "Male",
				"Ms": "Female"
			}[this.frm.doc.salutation]);
		}
	},

});
frappe.ui.form.on('Employee',{
	setup: function(frm) {
		frm.make_methods = {
			'Contract': () => frappe.model.open_mapped_doc({
				method: 'erpnext.hr.doctype.employee.employee.make_contract',
				frm: cur_frm
			})
		}

		frm.set_query("leave_policy", function() {
			return {
				"filters": {
					"docstatus": 1
				}
			};
		});
	},
	onload:function(frm) {
		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	},

	refresh: function(frm) {
		frm.add_custom_button(__("Grant Leaves"), () => {

			if (frm.doc.leave_policy){
				let d = new frappe.ui.Dialog({
					'fields': [
						{'label': 'Leave Period', 'fieldname': 'leave_period', 'fieldtype': 'Link', 'options':'Leave Period'},
						{'label': 'Add unused leaves from previous allocations', 'fieldname': 'carry_forward', 'fieldtype': 'Check', 'default': 0}
					],
					primary_action: function(){
						frm.events.grant_leaves(frm, d.get_values());
						d.hide();
					}
				});
				d.show();
			} else {
				frappe.throw({
					message: __("Please set Leave Policy for Employee: ") + frm.doc.employee,
					indicator: 'blue',
				});
			}
		});
	},
	grant_leaves: function(frm, data) {
		frappe.call({
			method: "erpnext.hr.doctype.employee.employee.grant_leaves",
			args: {
				employee: frm.doc.employee,
				joining_date: frm.doc.date_of_joining,

				leave_period: data.leave_period,
				carry_forward: data.carry_forward
			},
		});
	},
	prefered_contact_email:function(frm){		
		frm.events.update_contact(frm)		
	},
	personal_email:function(frm){
		frm.events.update_contact(frm)
	},
	company_email:function(frm){
		frm.events.update_contact(frm)
	},
	user_id:function(frm){
		frm.events.update_contact(frm)
	},
	update_contact:function(frm){
		var prefered_email_fieldname = frappe.model.scrub(frm.doc.prefered_contact_email) || 'user_id';
		frm.set_value("prefered_email",
			frm.fields_dict[prefered_email_fieldname].value)
	},
	status: function(frm) {
		return frm.call({
			method: "deactivate_sales_person",
			args: {
				employee: frm.doc.employee,
				status: frm.doc.status
			}
		});
	},
	reports_to: function(frm){
		frappe.call({
			method: "erpnext.hr.doctype.employee.employee.get_reports_to_email",
			args: { emp_id: frm.doc.reports_to },
			callback: function(r) {
				if (r && r.message) {
					frm.set_value("reports_to_email", r.message);
					refresh_field("reports_to_email");
				}
			}
		});
	},
	create_user: function(frm) {
		if (!frm.doc.prefered_email)
		{
			frappe.throw(__("Please enter Preferred Contact Email"))
		}
		frappe.call({
			method: "erpnext.hr.doctype.employee.employee.create_user",
			args: { employee: frm.doc.name, email: frm.doc.prefered_email },
			callback: function(r)
			{
				frm.set_value("user_id", r.message)
			}
		});
	}
});
cur_frm.cscript = new erpnext.hr.EmployeeController({frm: cur_frm});
