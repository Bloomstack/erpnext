# Copyright (c) 2013, Bloom Stack, Inc and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

from frappe import _
import frappe


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
			"fieldname": "total_sales",
			"label": _("Total Sales"),
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 200
		},
		{
			"fieldname": "total_expense",
			"label": _("Total Expense"),
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 200
		},
		{
			"fieldname": "net_gl",  # Net Gain/Loss
			"label": _("Net Gain/Loss"),
			"width": 200
		}
	]


def get_data(filters=None):
	data = frappe.db.sql("""
		SELECT
			c.customer_name AS customer_name,
			SUM(IFNULL(si.grand_total, 0)) AS total_sales,
			SUM(IFNULL(pi.grand_total, 0)) AS total_expense,
			SUM(IFNULL(si.grand_total, 0)) - SUM(IFNULL(pi.grand_total, 0)) AS net_gl
		FROM
			tabCustomer c
				JOIN tabSupplier s ON c.customer_name = s.supplier_name
				LEFT JOIN `tabSales Invoice` si ON si.customer = c.customer_name
				LEFT JOIN `tabPurchase Invoice` pi ON pi.supplier = c.customer_name
		GROUP BY
			c.customer_name
		""", as_dict=True)
	return data
