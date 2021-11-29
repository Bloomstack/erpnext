# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from erpnext.accounts.report.financial_statements import (get_period_list, get_columns, get_data)

def execute(filters=None):
	period_list = get_period_list(filters.from_date, filters.to_date,
		filters.periodicity, company=filters.company)

	currency = filters.presentation_currency or frappe.get_cached_value('Company',  filters.company,  "default_currency")

	asset = get_data(filters.company, "Asset", "Debit", period_list,
		only_current_fiscal_year=False, filters=filters,
		accumulated_values=filters.accumulated_values)

	liability = get_data(filters.company, "Liability", "Credit", period_list,
		only_current_fiscal_year=False, filters=filters,
		accumulated_values=filters.accumulated_values)

	equity = get_data(filters.company, "Equity", "Credit", period_list,
		only_current_fiscal_year=False, filters=filters,
		accumulated_values=filters.accumulated_values)

	provisional_profit_loss, total_credit = get_provisional_profit_loss(asset, liability, equity,
		period_list, filters.company, currency)

	message, opening_balance = check_opening_balance(asset, liability, equity)

	data = []
	#add assets to the balance sheet report
	data.extend(asset or [])

	#add liabilities to the balance sheet report
	data.extend(liability or [])

	#add provisional profit/loss and adjust equity totals if books are not closed
	if len(equity) > 2 and provisional_profit_loss:
		equity = append_provisions_to_equity(equity, provisional_profit_loss, period_list)
		data.extend(equity or [])

	#specific case when equity is completely empty but we still need to add
	elif not equity and provisional_profit_loss:
		equity = create_equity_with_provisions(provisional_profit_loss, period_list)
		data.extend(equity)

	#add equity to the balance sheet report if there are no provisional profits/losses
	else:
		data.extend(equity or [])

	if opening_balance and round(opening_balance,2) !=0:
		unclosed ={
			"account_name": "'" + _("Unclosed Fiscal Years Profit / Loss (Credit)") + "'",
			"account": "'" + _("Unclosed Fiscal Years Profit / Loss (Credit)") + "'",
			"warn_if_negative": True,
			"currency": currency
		}
		for period in period_list:
			unclosed[period.key] = opening_balance
			if provisional_profit_loss:
				provisional_profit_loss[period.key] = provisional_profit_loss[period.key] - opening_balance

		unclosed["total"]=opening_balance
		data.append(unclosed)

	if total_credit:
		data.append({})
		data.append(total_credit)

	columns = get_columns(filters.periodicity, period_list, filters.accumulated_values, company=filters.company)
	chart = get_chart_data(filters, columns, asset, liability, equity)

	return columns, data, message, chart

def append_provisions_to_equity(equity, provisional_profit_loss, period_list):
	"""
	Adding provisions to the equity accounts when other equity accounts have non-zero values.

	Args:
		equity (list): dicts containing equity accounts and their periodic balances
		provisional_profit_loss (dict): details of provisional profit / loss
		period_list (list): list of periods for which the data needs to be processed

	Returns:
		dict: details of equity account containing provisional profits / loss
	"""
	total_equity = equity[-2]
	provisional_profit_loss["indent"] = total_equity.get("indent") + 1
	equity.insert(-2, provisional_profit_loss) #add provisions to equity list
	equity.pop()
	for period in period_list:
		if period.key in total_equity and period.key in provisional_profit_loss:
			total_equity[period.key] = 0.0 if not total_equity[period.key] else total_equity[period.key]
			total_equity[period.key] += provisional_profit_loss[period.key] #update equity account total for all periods
	return equity



def create_equity_with_provisions(provisional_profit_loss, period_list):
	"""
	Adds line for provisional profit/loss if other equity accounts have zero balances.

	Args:
		provisional_profit_loss (dict): details of provisional profit / loss
		period_list (list): list of periods for which the data needs to be processed

	Returns:
		dict: details of equity account containing provisional profits / loss
	"""
	equity = [{"account_name": "Equity", "account": "Equity", "indent": 0.0, "is_group": 1.0}]
	provisional_profit_loss['parent_account']= "Equity"
	provisional_profit_loss["indent"] = 1.0
	equity.append(provisional_profit_loss)
	total_summary = {"account_name": "Total Equity", "account": "Total Equity", "indent": 0.0, "is_group": 0.0}
	for period in period_list:
		if period.key in provisional_profit_loss:
			total_summary[period.key] = provisional_profit_loss[period.key]
	equity.append(total_summary)
	equity.append({}) #blank line for better optics post adding the provisions to the equity summary
	return equity

def get_provisional_profit_loss(asset, liability, equity, period_list, company, companies=None, currency=None, consolidated=False):
	provisional_profit_loss = {}
	total_row = {}

	if asset and (liability or equity):
		total = total_row_total=0
		currency = currency or frappe.get_cached_value('Company',  company,  "default_currency")
		total_row = {
			"account_name": _("Total Liabilities and Equity"),
			"account": _("Total Liabilities and Equity"),
			"warn_if_negative": True,
			"currency": currency
		}
		has_value = False

		if consolidated:
			for company in companies:
				total = total_row_total=0
				has_value, provisional_profit_loss, total_row, total, total_row_total = add_periodicity_for_provisional_profit_loss(asset, liability, equity, period_list, provisional_profit_loss, total_row, total, total_row_total, has_value, consolidated, company)
		else:
			has_value, provisional_profit_loss, total_row, total, total_row_total = add_periodicity_for_provisional_profit_loss(asset, liability, equity, period_list, provisional_profit_loss, total_row, total, total_row_total, has_value, consolidated)

		if has_value:
			provisional_profit_loss.update({
				"account_name": _("Provisional Profit / Loss (Credit)") ,
				"account": _("Provisional Profit / Loss (Credit)"),
				"warn_if_negative": True,
				"currency": currency,
				"total": None,
				"is_group": 0.0,
				"has_value": True,
				"opening_balance": -0.0,
				"parent_account": "Equity"
			})

	return provisional_profit_loss, total_row

def add_periodicity_for_provisional_profit_loss(asset, liability, equity, period_list, provisional_profit_loss, total_row, total, total_row_total, has_value, consolidated, company=None):
	for period in period_list:
		if consolidated:
			key = f'{company}({period.key})'
		else:
			key = f'{period.key}'
		effective_liability = 0.0
		if liability:
			effective_liability += flt(liability[-2].get(key))
		if equity:
			effective_liability += flt(equity[-2].get(key))

		provisional_profit_loss[key] = flt(asset[-2].get(key)) - effective_liability
		total_row[key] = effective_liability + provisional_profit_loss[key]

		if provisional_profit_loss[key]:
			has_value = True

		total += flt(provisional_profit_loss[key])
		total_row_total += flt(total_row[key])
		if company:
			provisional_profit_loss[f"{company}(total)"] = total
			total_row[f"{company}(total)"] = total_row_total
		else:
			provisional_profit_loss["total"] = total
			total_row["total"] = total_row_total
	return has_value, provisional_profit_loss, total_row, total, total_row_total

def check_opening_balance(asset, liability, equity):
	# Check if previous year balance sheet closed
	opening_balance = 0
	float_precision = cint(frappe.db.get_default("float_precision")) or 2
	if asset:
		opening_balance = flt(asset[0].get("opening_balance", 0), float_precision)
	if liability:
		opening_balance -= flt(liability[0].get("opening_balance", 0), float_precision)
	if equity:
		opening_balance -= flt(equity[0].get("opening_balance", 0), float_precision)

	opening_balance = flt(opening_balance, float_precision)
	if opening_balance:
		return _("Previous Financial Year is not closed"), opening_balance
	return None, None

def get_chart_data(filters, columns, asset, liability, equity):
	labels = [d.get("label") for d in columns[2:]]

	asset_data, liability_data, equity_data = [], [], []

	for p in columns[2:]:
		if asset:
			asset_data.append(asset[-2].get(p.get("fieldname")))
		if liability:
			liability_data.append(liability[-2].get(p.get("fieldname")))
		if equity:
			equity_data.append(equity[-2].get(p.get("fieldname")))

	datasets = []
	if asset_data:
		datasets.append({'name': _('Assets'), 'values': asset_data})
	if liability_data:
		datasets.append({'name': _('Liabilities'), 'values': liability_data})
	if equity_data:
		datasets.append({'name': _('Equity'), 'values': equity_data})

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

	return chart