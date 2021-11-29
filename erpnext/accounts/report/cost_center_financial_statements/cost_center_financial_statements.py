# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from erpnext.accounts.report.financial_statements import get_cost_centers_with_children, get_period_list
from erpnext.accounts.report.consolidated_financial_statement.consolidated_financial_statement import get_balance_sheet_data, get_profit_loss_data

def execute(filters=None):
	columns, data, message, chart = [], [], [], []

	if not filters.get('company'):
		return columns, data, message, chart
	period_list = get_period_list(filters.from_date, filters.to_date,
		filters.periodicity, filters.accumulated_in_group_company)

	if not filters.get('cost_center'):
		frappe.msgprint(_("Please select at least one cost center."));

	if not filters.get('include_child_cost_centers'):
		cost_centers = filters.cost_center
	else:
		cost_centers = get_cost_centers_with_children(filters.cost_center)

	columns = get_columns(cost_centers, filters.periodicity, period_list)

	if filters.get('report') == "Balance Sheet":
		data, message, chart = get_balance_sheet_data(period_list, cost_centers, columns, filters, cost_center_wise=True)
	elif filters.get('report') == "Profit and Loss Statement":
		data, message, chart = get_profit_loss_data(period_list, cost_centers, columns, filters, cost_center_wise=True)

	return columns, data, message, chart

def get_columns(cost_centers, periodicity, period_list):
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
		for period in period_list:
			columns.append({
				"fieldname": f'{cost_center}({period.key})',
				"label": f'{cost_center}({period.label})',
				"fieldtype": "Currency",
				"options": "currency",
				"width": 150
			})
		if periodicity!="Yearly":
			columns.append({
				"fieldname": f"{cost_center}(total)",
				"label": f'{cost_center} Total',
				"fieldtype": "Currency",
				"width": 150
			})
	
	return columns

