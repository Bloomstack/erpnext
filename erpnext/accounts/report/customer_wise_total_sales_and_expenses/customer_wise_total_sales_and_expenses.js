// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer-wise Total Sales and Expenses"] = {
	"formatter": function (value, row, column, data, default_formatter) {
		if (column.fieldname == "total_sales" && data && !!data["total_sales"]) {
			value = data["total_sales"];
			column.link_onclick = "frappe.query_reports['Customer-wise Total Sales and Expenses'].set_total_sales_route_to_sales_register(" + JSON.stringify(data) + ")";
		}
		if (column.fieldname == "total_purchase" && data && !!data["total_purchase"]) {
			value = data["total_purchase"];
			column.link_onclick = "frappe.query_reports['Customer-wise Total Sales and Expenses'].set_total_expenses_route_to_purchase_register(" + JSON.stringify(data) + ")";
		}
		value = default_formatter(value, row, column, data);
		return value;
	},
	"set_total_sales_route_to_sales_register": function (data) {
		frappe.route_options = {
			"customer": data["customer_name"]
		};
		frappe.set_route("query-report", "Sales Register");
	},
	"set_total_expenses_route_to_purchase_register": function (data) {
		frappe.route_options = {
			"supplier": data["customer_name"]
		};
		frappe.set_route("query-report", "Purchase Register");
	}
};