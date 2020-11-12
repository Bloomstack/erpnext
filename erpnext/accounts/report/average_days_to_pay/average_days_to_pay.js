// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Average Days to Pay"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "finance_book",
			label: __("Finance Book"),
			fieldtype: "Link",
			options: "Finance Book",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
			width: "60px",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
			width: "60px",
		},
		{
			fieldname: "account",
			label: __("Account"),
			fieldtype: "Link",
			options: "Account",
			get_query: function () {
				var company = frappe.query_report.get_filter_value("company");
				return {
					doctype: "Account",
					filters: {
						company: company,
					},
				};
			},
		},
		{
			fieldtype: "Break",
		},
		{
			fieldname: "party_type",
			label: __("Party Type"),
			fieldtype: "Link",
			options: "Party Type",
			default: "",
			on_change: function (report) {
				frappe.query_report.set_filter_value("party", "");
				get_addresses(report);
			},
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "Link",
			get_options: function () {
				let party_type = frappe.query_report.get_filter_value('party_type');
				return party_type;
			},
			on_change: function (report) {
				let party_type = frappe.query_report.get_filter_value("party_type");
				let party = frappe.query_report.get_filter_value("party");

				if (!party_type) {
					frappe.query_report.set_filter_value("party_name", "");
					return;
				} else {
					let fieldname = erpnext.utils.get_party_name(party_type) || "name";
					frappe.db.get_value(party_type, party, fieldname, function (value) {
						frappe.query_report.set_filter_value(
							"party_name",
							value[fieldname]
						);
					});
				}

				get_addresses(report);
			},
		},
		{
			fieldname: "party_name",
			label: __("Party Name"),
			fieldtype: "Data",
			hidden: 1,
		},
	],
};

erpnext.utils.add_dimensions("Statement of Account", 15);

function get_addresses(report) {
	let filters = report.get_filter_values();

	if (!filters.company || !filters.party_type || !filters.party[0]) {
		return;
	}

	frappe.call({
		method:
			"erpnext.accounts.report.statement_of_account.statement_of_account.get_addresses",
		args: {
			company: filters.company,
			party_type: filters.party_type,
			party: filters.party[0],
		},
		callback: function (r) {
			report.addresses = r.message;
		},
	});
}
