# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data


def get_columns(filters):
	return [
		{
			"fieldname": "customer_name",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 200
		},
		{
			"fieldname": "monthly_sales_target",
			"label": _("Monthly Sales Target"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "total_monthly_sales",
			"label": _("Total Monthly Sales"),
			"fieldtype": "Currency",
			"width": 150
		}
	]


def get_data(filters=None):
	return frappe.db.sql("""
		SELECT
			customer_name,
			monthly_sales_target,
			total_monthly_sales
		FROM
			tabCustomer
		WHERE
			monthly_sales_target > total_monthly_sales
		""")
