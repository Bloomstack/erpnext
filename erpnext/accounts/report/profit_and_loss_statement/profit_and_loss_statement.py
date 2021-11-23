# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext import get_default_company
from erpnext.accounts.utils import get_company_default
from erpnext.accounts.report.financial_statements import (get_period_list, get_columns, get_data)

def execute(filters=None):
	period_list = get_period_list(filters.from_date, filters.to_date,
		filters.periodicity, filters.accumulated_values, filters.company)

	ignore_accumulated_values_for_fy = True
	if filters.periodicity == "Custom":
		ignore_accumulated_values_for_fy=False

	#fetch data for the income and expense accounts
	income = get_data(filters.company, "Income", "Credit", period_list, filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True, ignore_accumulated_values_for_fy=ignore_accumulated_values_for_fy)

	expense = get_data(filters.company, "Expense", "Debit", period_list, filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True, ignore_accumulated_values_for_fy=ignore_accumulated_values_for_fy)

	#add the section for income
	data = []
	data.extend(income or [])

	#get direct and indirect expense account names
	gross_profit_loss = None
	direct_expense_account = frappe.get_value("Company", get_default_company(), "default_direct_expenses")
	indirect_expense_account = frappe.get_value("Company", get_default_company(), "default_indirect_expenses")
	company_abbr = get_company_default(get_default_company(), "abbr")
	direct_expenses = None

	for expense_item in expense:
		data.append(expense_item)

		#add gross profit line item on the PL statement
		if expense_item.get("group_account_summary", False) and expense_item.get("_account") == direct_expense_account:
			direct_expenses = expense_item
			gross_profit_loss = get_profit_loss(income, expense_item, period_list, filters.company,
									"Gross Profit", indent=1, is_group=0)
			if gross_profit_loss:
				data.append(gross_profit_loss)
				gross_profit_loss = None

		#add the line for net operating income / loss
		if expense_item.get("group_account_summary", False) and expense_item.get("_account") == indirect_expense_account:
			operating_profit_loss = get_profit_loss(income, expense_item, period_list, filters.company,
										"Net Operating Profit", indent=expense_item.get("indent"), is_group=0, direct_expenses=direct_expenses)
			if operating_profit_loss:
				data.append(operating_profit_loss)
				operating_profit_loss = None

	#add the line for net profit / loss
	net_profit_loss = get_net_profit_loss(income, expense, period_list, filters.company, filters.presentation_currency)
	if net_profit_loss:
		data.append(net_profit_loss)

	columns = get_columns(filters.periodicity, period_list, filters.accumulated_values, filters.company)
	chart = get_chart_data(filters, columns, income, expense, net_profit_loss)

	return columns, data, None, chart

def get_profit_loss(income, expense_item, period_list, company, account_name, indent, is_group, direct_expenses=None, currency=None, consolidated=False):
	"""
	Add the summary line for gross profit in the profit and loss financial statement.

	Args:
		income (list of dict): Contains all the income account rows and summaries
		expense (list of dict): Contains all the expense account rows and summaries
		period_list (list): all the periods for which we have income and expense data
		company (string): name of the company
		account_name (string): gross profit or net operating profit account name
		currency (string, optional): Currency. Defaults to None.
		consolidated (bool, optional): Whether the statements are consolidated or company-wise. Defaults to False.
	"""
	gross_total = 0
	profit_loss = {
		"account_name": _(account_name),
		"account": _(account_name),
		"is_group": is_group,
		"indent": indent,
		"warn_if_negative": True,
		"currency": currency or frappe.get_cached_value('Company',  company,  "default_currency")
	}
	has_value = False
	total_direct_expense = expense_item

	for period in period_list:
		key = period if consolidated else period.key
		total_income = flt(income[-2][key], 3) if income else 0
		total_expense = flt(total_direct_expense[key],3) if expense_item else 0

		profit_loss[key] = total_income - total_expense

		#subtract direct expenses as well from the total for net operating profit
		if direct_expenses:
			profit_loss[key] -= direct_expenses[key]

		if profit_loss[key]:
			has_value = True

		gross_total += flt(profit_loss[key])
		profit_loss["total"] = gross_total

	if has_value:
		return profit_loss


def get_net_profit_loss(income, expense, period_list, company, companies=None, currency=None, consolidated=False):
	total = 0
	net_profit_loss = {
		"account_name": "'" + _("Profit for the year") + "'",
		"account": "'" + _("Profit for the year") + "'",
		"warn_if_negative": True,
		"currency": currency or frappe.get_cached_value('Company',  company,  "default_currency")
	}

	has_value = False
	if consolidated:
		for company in companies:
			for period in period_list:
				key = f'{company}({period.key})'
				total_income = flt(income[-2][key], 3) if income else 0
				total_expense = flt(expense[-2][key], 3) if expense else 0

				net_profit_loss[key] = total_income - total_expense

				if net_profit_loss[key]:
					has_value=True

				total += flt(net_profit_loss[key])
				net_profit_loss["total"] = total
	else:

		for period in period_list:
			key = period if consolidated else period.key
			total_income = flt(income[-2][key], 3) if income else 0
			total_expense = flt(expense[-2][key], 3) if expense else 0

			net_profit_loss[key] = total_income - total_expense

			if net_profit_loss[key]:
				has_value=True

			total += flt(net_profit_loss[key])
			net_profit_loss["total"] = total

	if has_value:
		return net_profit_loss

def get_chart_data(filters, columns, income, expense, net_profit_loss):
	labels = [d.get("label") for d in columns[2:]]

	income_data, expense_data, net_profit = [], [], []

	for p in columns[2:]:
		if income:
			income_data.append(income[-2].get(p.get("fieldname")))
		if expense:
			expense_data.append(expense[-2].get(p.get("fieldname")))
		if net_profit_loss:
			net_profit.append(net_profit_loss.get(p.get("fieldname")))

	datasets = []
	if income_data:
		datasets.append({'name': _('Income'), 'values': income_data})
	if expense_data:
		datasets.append({'name': _('Expense'), 'values': expense_data})
	if net_profit:
		datasets.append({'name': _('Net Profit/Loss'), 'values': net_profit})

	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		}
	}

	if not filters.accumulated_values:
		chart["type"] = "bar"
	else:
		chart["type"] = "line"

	chart["fieldtype"] = "Currency"

	return chart