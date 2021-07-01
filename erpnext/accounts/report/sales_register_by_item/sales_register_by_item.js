// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Sales Register By Item"] = {
	"filters": [
		{
			"fieldname": "start_date",
			"label": __("Start Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(),-1),
			"reqd": 1
		},
		{
			"fieldname": "end_date",
			"label": __("End Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "item_name",
			"label": __("Item Name"),
			"fieldtype": "Link",
			"options": "Item"

		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "mode_of_payment",
			"label": __("Mode of Payment"),
			"fieldtype": "Link",
			"options": "Mode of Payment"
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse"
		},
		{
			"label": __("Group By"),
			"fieldname": "group_by",
			"fieldtype": "Select",
			"options": ["Customer", "Item"]
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold) {
			value = value.bold();

		}
		return value;
	}
}
