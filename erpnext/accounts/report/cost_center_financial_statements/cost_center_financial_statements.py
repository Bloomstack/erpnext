# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from erpnext.accounts.report.financial_statements import get_cost_centers_with_children
from erpnext.accounts.report.consolidated_financial_statement.consolidated_financial_statement import get_balance_sheet_data, get_profit_loss_data

def execute(filters=None):
	columns, data, message, chart = [], [], [], []

	if not filters.get('company'):
		return columns, data, message, chart
	period_dict = {}
	period_dict.update({
		'year_start_date': filters.get('from_date'),
		'year_end_date': filters.get('to_date')
	})

	if not filters.get('cost_center'):
		frappe.msgprint(_("Please select at least one cost center."));

	cost_centers = get_cost_centers_with_children(filters.cost_center)
	columns = get_columns(cost_centers)

	if filters.get('report') == "Balance Sheet":
		data, message, chart = get_balance_sheet_data(period_dict, cost_centers, columns, filters, cost_center_wise=True)
	elif filters.get('report') == "Profit and Loss Statement":
		data, message, chart = get_profit_loss_data(period_dict, cost_centers, columns, filters, cost_center_wise=True)

	return columns, data, message, chart

def get_columns(cost_centers):
	columns = [{
		"fieldname": "account",
		"label": _("Account"),
		"fieldtype": "Link",
		"options": "Account",
		"width": 300
	},
	{
		"fieldname": "currency",
		"label": _("Currency"),
		"fieldtype": "Link",
		"options": "Currency",
		"hidden": 1
	}]

	for cost_center in cost_centers:
		columns.append({
			"fieldname": cost_center,
			"label": cost_center,
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		})
	
	columns.append({
		"fieldname": "total",
		"label": _("Total"),
		"fieldtype": "Currency",
		"options": "Currency",
		"width": 150
	})

	return columns

